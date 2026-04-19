"""
models.py
---------
Domain dataclasses for the AI-Powered MCQ Quiz module.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class QuizQuestion:
    """A single multiple-choice question."""

    question: str
    options: List[str]   # always 4 options (A–D)
    answer: str          # correct option letter, e.g. "B"
    skill_tag: str       # which skill this question tests

    def is_correct(self, response: str) -> bool:
        """Check if a given response letter matches the correct answer."""
        return response.strip().upper() == self.answer.strip().upper()


@dataclass
class QuizResult:
    """Scored outcome of a quiz submission."""

    employee_id: str
    score: int           # number of correct answers
    total: int
    pct: float           # score / total * 100
    details: List[dict] = field(default_factory=list)  # per-question breakdown
