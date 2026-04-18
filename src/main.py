"""
main.py
-------
Core pipeline for the Smart Resource Matcher.

Orchestrates the full flow:
    resume file → text extraction → skill extraction →
    employee matching → ranking → availability scheduling

The :func:`run_pipeline` function is the single entry point used
by both the Streamlit UI and the FastAPI REST layer.
"""

from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

from src.config.settings import DEFAULT_TOP_N, DEFAULT_SLOT_DURATION
from src.data_loader.loader import load_employees, load_schedules
from src.resume_parser.parser import extract_text
from src.resume_parser.skill_extractor import extract_skills
from src.utils.text_utils import build_skill_vocabulary
from src.matcher.skill_matcher import match_employees
from src.matcher.ranking import rank_employees
from src.scheduler.availability import get_availability


# ── Module-level caches ──────────────────────────────────────────────────────
# Loaded once and reused across pipeline calls for performance.

_employees_df: Optional[pd.DataFrame] = None
_schedules_df: Optional[pd.DataFrame] = None
_skill_vocab: Optional[set] = None


def _load_data() -> None:
    """Load employees + schedules into module-level caches (lazy singleton)."""
    global _employees_df, _schedules_df, _skill_vocab

    if _employees_df is None:
        _employees_df = load_employees()

    if _schedules_df is None:
        _schedules_df = load_schedules()

    if _skill_vocab is None:
        _skill_vocab = build_skill_vocabulary(_employees_df["skills"])


def get_employees_df() -> pd.DataFrame:
    """Return the cached employees DataFrame (loading if needed)."""
    _load_data()
    return _employees_df  # type: ignore[return-value]


def get_schedules_df() -> pd.DataFrame:
    """Return the cached schedules DataFrame (loading if needed)."""
    _load_data()
    return _schedules_df  # type: ignore[return-value]


def get_vocab() -> set:
    """Return the cached skill vocabulary set (loading if needed)."""
    _load_data()
    return _skill_vocab  # type: ignore[return-value]


# ── Public pipeline ──────────────────────────────────────────────────────────

def run_pipeline(
    resume_path: Union[str, Path],
    target_date: Union[date, str],
    top_n: int = DEFAULT_TOP_N,
    slot_duration: int = DEFAULT_SLOT_DURATION,
) -> Dict[str, Any]:
    """
    Run the full Smart Resource Matcher pipeline.

    Parameters
    ----------
    resume_path : str | Path
        Path to a PDF or DOCX resume file.
    target_date : date | str
        Calendar date to check employee availability.
    top_n : int
        Maximum number of matched employees to return.
    slot_duration : int
        Minimum free-slot length in minutes.

    Returns
    -------
    dict
        Keys:

        - ``extracted_skills`` — List[str] of skills found in the resume
        - ``matched_employees`` — pd.DataFrame of top-N ranked employees
        - ``availability`` — Dict[str, List[Tuple]] mapping employee_id
          to free time-slot tuples ``(start, end)``
    """
    # 1. Load data (cached after first call)
    _load_data()
    employees = _employees_df  # type: ignore[assignment]
    schedules = _schedules_df  # type: ignore[assignment]
    vocab = _skill_vocab       # type: ignore[assignment]

    # 2. Extract text from resume
    raw_text = extract_text(resume_path)

    # 3. Extract skills
    extracted_skills: List[str] = extract_skills(raw_text, vocab)

    # 4. Match & rank
    matched = match_employees(extracted_skills, employees)
    ranked = rank_employees(matched, top_n=top_n)

    # 5. Get availability for the matched employees
    employee_ids: List[str] = ranked["employee_id"].tolist() if not ranked.empty else []
    avail = get_availability(employee_ids, schedules, target_date, slot_duration)

    return {
        "extracted_skills": extracted_skills,
        "matched_employees": ranked,
        "availability": avail,
    }
