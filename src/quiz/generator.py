"""
generator.py
------------
AI-powered MCQ quiz generation using the Groq Chat Completions API.

Builds a carefully engineered prompt, sends it to Groq's free-tier LLM,
and parses the structured JSON response into QuizQuestion objects.
"""

import json
import logging
from typing import List, Optional

from src.quiz.models import QuizQuestion

logger = logging.getLogger(__name__)


def _build_prompt(
    required_skills: List[str],
    job_context: str = "",
    n_questions: int = 5,
) -> str:
    """
    Build the system + user prompt for quiz generation.

    The prompt asks the LLM to return a JSON array of question objects,
    ensuring reliable, parseable output without regex hacks.
    """
    skills_str = ", ".join(required_skills)
    context_line = f"\nJob context: {job_context}" if job_context.strip() else ""

    return f"""You are a technical quiz generator. Create exactly {n_questions} multiple-choice questions
to test a candidate's knowledge of these skills: {skills_str}.{context_line}

RULES:
1. Each question must test ONE specific skill from the list.
2. Distribute questions across as many skills as possible.
3. Provide exactly 4 options labelled A, B, C, D.
4. Exactly one option must be correct.
5. Questions should be practical, not trivia — test real working knowledge.
6. Vary difficulty: mix easy, medium, and hard questions.

Return ONLY a valid JSON array. No markdown, no explanation, no code fences.
Each element must have exactly these keys:
  "question"  — the question text
  "options"   — array of 4 strings ["A. ...", "B. ...", "C. ...", "D. ..."]
  "answer"    — the correct letter (e.g. "B")
  "skill_tag" — which skill from the list this tests

Example format:
[
  {{
    "question": "What does CSS flexbox do?",
    "options": ["A. Database queries", "B. Flexible layouts", "C. Server routing", "D. File I/O"],
    "answer": "B",
    "skill_tag": "css"
  }}
]"""


def _parse_response(raw_text: str) -> List[dict]:
    """
    Parse the LLM response into a list of question dicts.

    Handles common LLM quirks: markdown fences, trailing commas, etc.
    """
    text = raw_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        # Remove opening fence (```json or ```)
        first_newline = text.index("\n")
        text = text[first_newline + 1:]
    if text.endswith("```"):
        text = text[:-3].rstrip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.error("Failed to parse LLM response as JSON:\n%s", text[:500])
        raise ValueError(
            "LLM returned invalid JSON. Please try again."
        )

    if not isinstance(data, list):
        raise ValueError("Expected a JSON array of questions.")

    return data


def _dict_to_question(d: dict) -> QuizQuestion:
    """Convert a raw dict from the LLM into a QuizQuestion dataclass."""
    return QuizQuestion(
        question=str(d.get("question", "")),
        options=list(d.get("options", [])),
        answer=str(d.get("answer", "")).strip().upper(),
        skill_tag=str(d.get("skill_tag", "")),
    )


def generate_quiz(
    required_skills: List[str],
    job_context: str = "",
    n_questions: int = 5,
    _client: Optional[object] = None,
) -> List[QuizQuestion]:
    """
    Generate an MCQ quiz tailored to the given skills.

    Parameters
    ----------
    required_skills : list[str]
        Skills to test (e.g. ["python", "sql", "docker"]).
    job_context : str
        Optional one-line job description for better question relevance.
    n_questions : int
        Number of questions to generate (5–10).
    _client : optional
        Injected Groq client for testing. If None, creates a real client.

    Returns
    -------
    list[QuizQuestion]
        Parsed quiz questions ready for display / evaluation.

    Raises
    ------
    RuntimeError
        If the Groq API key is missing or the API call fails.
    ValueError
        If the LLM response cannot be parsed.
    """
    from src.config.settings import GROQ_API_KEY, GROQ_MODEL, QUIZ_MIN_Q, QUIZ_MAX_Q

    n_questions = max(QUIZ_MIN_Q, min(n_questions, QUIZ_MAX_Q))

    if not required_skills:
        return []

    # Build prompt
    prompt = _build_prompt(required_skills, job_context, n_questions)

    # Create or use injected client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to your .env file or "
                "environment variables to use the quiz feature."
            )
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
    else:
        client = _client

    # Call Groq
    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise technical quiz generator. "
                               "Return ONLY valid JSON arrays, nothing else.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=4096,
        )
    except Exception as exc:
        logger.error("Groq API call failed: %s", exc)
        raise RuntimeError(f"Groq API error: {exc}") from exc

    raw_text = chat_completion.choices[0].message.content
    question_dicts = _parse_response(raw_text)

    return [_dict_to_question(d) for d in question_dicts]
