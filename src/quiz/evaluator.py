"""
evaluator.py
------------
Quiz scoring logic for the Smart Resource Matcher.

Compares submitted answers against correct answers and produces
a detailed QuizResult with per-question breakdown.
"""

from typing import Dict, List

from src.quiz.models import QuizQuestion, QuizResult


def evaluate_quiz(
    questions: List[QuizQuestion],
    answers: Dict[int, str],
    employee_id: str,
) -> QuizResult:
    """
    Score a submitted quiz.

    Parameters
    ----------
    questions : list[QuizQuestion]
        The quiz questions (with correct answers).
    answers : dict[int, str]
        Submitted answers keyed by question index (0-based).
        Values are option letters like "A", "B", "C", "D".
    employee_id : str
        ID of the employee who took the quiz.

    Returns
    -------
    QuizResult
        Score, percentage, and per-question breakdown.
    """
    if not questions:
        return QuizResult(
            employee_id=employee_id,
            score=0,
            total=0,
            pct=0.0,
            details=[],
        )

    correct = 0
    details: List[dict] = []

    for idx, q in enumerate(questions):
        submitted = answers.get(idx, "")
        is_right = q.is_correct(submitted)
        if is_right:
            correct += 1

        details.append({
            "index": idx,
            "question": q.question,
            "skill_tag": q.skill_tag,
            "correct_answer": q.answer,
            "submitted_answer": submitted.strip().upper() if submitted else "",
            "is_correct": is_right,
        })

    total = len(questions)
    pct = round((correct / total) * 100, 1) if total > 0 else 0.0

    return QuizResult(
        employee_id=employee_id,
        score=correct,
        total=total,
        pct=pct,
        details=details,
    )
