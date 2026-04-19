"""
quiz — AI-Powered MCQ Quiz module for Smart Resource Matcher.

Exports
-------
QuizQuestion    — dataclass for a single MCQ question
QuizResult      — dataclass for a scored quiz outcome
generate_quiz   — generate quiz via Groq API
evaluate_quiz   — score submitted answers
"""

from src.quiz.models import QuizQuestion, QuizResult
from src.quiz.generator import generate_quiz
from src.quiz.evaluator import evaluate_quiz

__all__ = ["QuizQuestion", "QuizResult", "generate_quiz", "evaluate_quiz"]
