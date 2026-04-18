"""
api/app.py
----------
FastAPI REST layer for the Smart Resource Matcher.

Endpoints
---------
POST /analyze
    Upload a resume file (PDF/DOCX), returns extracted skills,
    matched employees, and availability.

GET /employees
    List all employees in the dataset.

GET /availability/{employee_id}
    Get free time slots for a specific employee on a given date.

POST /quiz/generate
    Generate an MCQ quiz for given skills.

POST /quiz/submit
    Submit quiz answers and get scored results.
"""

import tempfile
from datetime import date, time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, File, Query, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.config.settings import DEFAULT_TOP_N, DEFAULT_SLOT_DURATION
from src.main import get_employees_df, get_schedules_df, get_vocab, run_pipeline
from src.quiz.generator import generate_quiz
from src.quiz.evaluator import evaluate_quiz
from src.scheduler.availability import get_availability as _get_availability


app = FastAPI(
    title="Smart Resource Matcher API",
    description="Match resumes to employees by skills and check availability.",
    version="1.0.0",
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _time_slots_to_json(
    slots: List[Tuple[time, time]],
) -> List[Dict[str, str]]:
    """Convert a list of (start, end) time tuples to JSON-friendly dicts."""
    return [
        {"start": s.strftime("%H:%M"), "end": e.strftime("%H:%M")}
        for s, e in slots
    ]


# ── POST /analyze ────────────────────────────────────────────────────────────

@app.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    target_date: str = Query(..., description="Target date (YYYY-MM-DD)"),
    top_n: int = Query(DEFAULT_TOP_N, ge=1, le=100),
    slot_duration: int = Query(DEFAULT_SLOT_DURATION, ge=15, le=480),
) -> Dict[str, Any]:
    """
    Upload a resume and get skill matches + employee availability.
    """
    # Validate file extension
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".pdf", ".docx"):
        return JSONResponse(
            status_code=400,
            content={"error": f"Unsupported file type '{suffix}'. Use .pdf or .docx"},
        )

    # Save uploaded file to a temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        result = run_pipeline(
            resume_path=tmp_path,
            target_date=target_date,
            top_n=top_n,
            slot_duration=slot_duration,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    # Serialise DataFrames and time objects for JSON
    matched_df = result["matched_employees"]
    employees_list = []
    if not matched_df.empty:
        for _, row in matched_df.iterrows():
            employees_list.append({
                "employee_id": row["employee_id"],
                "name": row["name"],
                "department": row.get("department", ""),
                "designation": row.get("designation", ""),
                "experience_years": float(row["experience_years"]),
                "matched_skills": row["matched_skills"],
                "match_count": int(row["match_count"]),
                "score": round(float(row["score"]), 4),
            })

    availability_json = {
        emp_id: _time_slots_to_json(slots)
        for emp_id, slots in result["availability"].items()
    }

    return {
        "extracted_skills": result["extracted_skills"],
        "matched_employees": employees_list,
        "availability": availability_json,
    }


# ── GET /employees ───────────────────────────────────────────────────────────

@app.get("/employees")
def list_employees() -> Dict[str, Any]:
    """List all employees in the dataset."""
    df = get_employees_df()
    employees = []
    for _, row in df.iterrows():
        employees.append({
            "employee_id": row["employee_id"],
            "name": row["name"],
            "department": row["department"],
            "designation": row["designation"],
            "skills": row["skills_list"],
            "experience_years": float(row["experience_years"]),
        })

    return {"count": len(employees), "employees": employees}


# ── GET /availability/{employee_id} ──────────────────────────────────────────

@app.get("/availability/{employee_id}")
def employee_availability(
    employee_id: str,
    target_date: str = Query(..., description="Target date (YYYY-MM-DD)"),
    slot_duration: int = Query(DEFAULT_SLOT_DURATION, ge=15, le=480),
) -> Dict[str, Any]:
    """Get free time slots for a specific employee on a given date."""
    schedules = get_schedules_df()
    avail = _get_availability(
        employee_ids=[employee_id],
        schedules_df=schedules,
        target_date=target_date,
        slot_duration=slot_duration,
    )

    slots = avail.get(employee_id, [])
    return {
        "employee_id": employee_id,
        "target_date": target_date,
        "slot_duration_minutes": slot_duration,
        "free_slots": _time_slots_to_json(slots),
    }


# ── Quiz request models ──────────────────────────────────────────────────────

class QuizGenerateRequest(BaseModel):
    skills: List[str] = Field(..., min_length=1, description="Skills to quiz on")
    job_context: str = Field("", description="Optional job context")
    n_questions: int = Field(5, ge=1, le=10)


class QuizSubmitRequest(BaseModel):
    employee_id: str
    answers: Dict[int, str] = Field(..., description="{question_index: 'A'/'B'/'C'/'D'}")


# ── POST /quiz/generate ──────────────────────────────────────────────────────

@app.post("/quiz/generate")
def quiz_generate(body: QuizGenerateRequest) -> Dict[str, Any]:
    """Generate an MCQ quiz tailored to the given skills."""
    try:
        questions = generate_quiz(
            required_skills=body.skills,
            job_context=body.job_context,
            n_questions=body.n_questions,
        )
    except RuntimeError as exc:
        return JSONResponse(status_code=503, content={"error": str(exc)})

    # Store in a simple in-memory cache for submission
    quiz_id = hash(tuple(q.question for q in questions)) & 0xFFFFFFFF
    _quiz_cache[quiz_id] = questions

    return {
        "quiz_id": quiz_id,
        "n_questions": len(questions),
        "questions": [
            {
                "index": i,
                "question": q.question,
                "options": q.options,
                "skill_tag": q.skill_tag,
            }
            for i, q in enumerate(questions)
        ],
    }


# ── POST /quiz/submit ────────────────────────────────────────────────────────

# Simple in-memory quiz cache (maps quiz_id -> list of QuizQuestion)
_quiz_cache: Dict[int, list] = {}


class QuizSubmitWithIdRequest(BaseModel):
    quiz_id: int
    employee_id: str
    answers: Dict[int, str] = Field(..., description="{question_index: 'A'/'B'/'C'/'D'}")


@app.post("/quiz/submit")
def quiz_submit(body: QuizSubmitWithIdRequest) -> Dict[str, Any]:
    """Submit quiz answers and get scored results."""
    questions = _quiz_cache.get(body.quiz_id)
    if questions is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Quiz ID {body.quiz_id} not found. Generate a quiz first."},
        )

    result = evaluate_quiz(
        questions=questions,
        answers=body.answers,
        employee_id=body.employee_id,
    )

    return {
        "employee_id": result.employee_id,
        "score": result.score,
        "total": result.total,
        "percentage": result.pct,
        "details": result.details,
    }
