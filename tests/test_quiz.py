"""
test_quiz.py
------------
Unit tests for the Phase 6 AI-Powered MCQ Quiz module.

All Groq API calls are mocked — no external network required.
"""

import json
from dataclasses import asdict
from unittest.mock import MagicMock, patch

import pytest

from src.quiz.models import QuizQuestion, QuizResult
from src.quiz.generator import generate_quiz, _parse_response, _dict_to_question
from src.quiz.evaluator import evaluate_quiz


# ── Fixtures ─────────────────────────────────────────────────────────────────

SAMPLE_JSON = json.dumps([
    {
        "question": "What is a Python decorator?",
        "options": [
            "A. A design pattern for classes",
            "B. A function that wraps another function",
            "C. A type of variable",
            "D. A loop construct",
        ],
        "answer": "B",
        "skill_tag": "python",
    },
    {
        "question": "Which SQL keyword filters grouped results?",
        "options": [
            "A. WHERE",
            "B. GROUP BY",
            "C. HAVING",
            "D. ORDER BY",
        ],
        "answer": "C",
        "skill_tag": "sql",
    },
    {
        "question": "What does Docker Compose do?",
        "options": [
            "A. Builds Docker images",
            "B. Runs multi-container applications",
            "C. Deploys to Kubernetes",
            "D. Monitors containers",
        ],
        "answer": "B",
        "skill_tag": "docker",
    },
])


@pytest.fixture
def sample_questions() -> list[QuizQuestion]:
    """Three well-formed quiz questions for testing."""
    return [
        QuizQuestion(
            question="What is a Python decorator?",
            options=["A. Design pattern", "B. Function wrapper", "C. Variable", "D. Loop"],
            answer="B",
            skill_tag="python",
        ),
        QuizQuestion(
            question="SQL HAVING filters?",
            options=["A. WHERE", "B. GROUP BY", "C. HAVING", "D. ORDER BY"],
            answer="C",
            skill_tag="sql",
        ),
        QuizQuestion(
            question="Docker Compose does?",
            options=["A. Builds images", "B. Multi-container apps", "C. K8s deploy", "D. Monitor"],
            answer="B",
            skill_tag="docker",
        ),
    ]


def _mock_groq_client(response_text: str) -> MagicMock:
    """Create a mock Groq client that returns the given response text."""
    client = MagicMock()
    choice = MagicMock()
    choice.message.content = response_text
    completion = MagicMock()
    completion.choices = [choice]
    client.chat.completions.create.return_value = completion
    return client


# ══════════════════════════════════════════════════════════════════════════════
# Test: Models
# ══════════════════════════════════════════════════════════════════════════════

class TestQuizModels:

    def test_quiz_question_is_correct(self):
        q = QuizQuestion("Q?", ["A", "B", "C", "D"], "B", "python")
        assert q.is_correct("B")
        assert q.is_correct("b")
        assert q.is_correct(" B ")
        assert not q.is_correct("A")

    def test_quiz_result_dataclass(self):
        r = QuizResult("E001", 3, 5, 60.0, [])
        assert r.employee_id == "E001"
        assert r.pct == 60.0


# ══════════════════════════════════════════════════════════════════════════════
# Test: Generator — response parsing
# ══════════════════════════════════════════════════════════════════════════════

class TestParseResponse:

    def test_clean_json(self):
        result = _parse_response(SAMPLE_JSON)
        assert len(result) == 3
        assert result[0]["answer"] == "B"

    def test_json_with_code_fences(self):
        fenced = f"```json\n{SAMPLE_JSON}\n```"
        result = _parse_response(fenced)
        assert len(result) == 3

    def test_json_with_bare_fences(self):
        fenced = f"```\n{SAMPLE_JSON}\n```"
        result = _parse_response(fenced)
        assert len(result) == 3

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="invalid JSON"):
            _parse_response("This is not JSON at all")

    def test_non_array_raises(self):
        with pytest.raises(ValueError, match="JSON array"):
            _parse_response('{"key": "value"}')


class TestDictToQuestion:

    def test_basic_conversion(self):
        d = {
            "question": "Q?",
            "options": ["A. X", "B. Y", "C. Z", "D. W"],
            "answer": "c",
            "skill_tag": "python",
        }
        q = _dict_to_question(d)
        assert q.answer == "C"
        assert len(q.options) == 4

    def test_missing_fields_default(self):
        q = _dict_to_question({})
        assert q.question == ""
        assert q.options == []
        assert q.answer == ""


# ══════════════════════════════════════════════════════════════════════════════
# Test: Generator — full generate_quiz flow (mocked)
# ══════════════════════════════════════════════════════════════════════════════

class TestGenerateQuiz:

    def test_mock_generation(self):
        client = _mock_groq_client(SAMPLE_JSON)
        questions = generate_quiz(
            required_skills=["python", "sql", "docker"],
            n_questions=3,
            _client=client,
        )
        assert len(questions) == 3
        assert all(isinstance(q, QuizQuestion) for q in questions)
        assert questions[0].skill_tag == "python"

    def test_empty_skills_returns_empty(self):
        result = generate_quiz(required_skills=[], n_questions=5)
        assert result == []

    def test_missing_api_key_raises(self):
        with patch("src.config.settings.GROQ_API_KEY", ""):
            with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
                generate_quiz(
                    required_skills=["python"],
                    n_questions=5,
                    _client=None,
                )

    def test_api_failure_raises_runtime_error(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = Exception("API down")
        with pytest.raises(RuntimeError, match="Groq API error"):
            generate_quiz(
                required_skills=["python"],
                n_questions=5,
                _client=client,
            )


# ══════════════════════════════════════════════════════════════════════════════
# Test: Evaluator
# ══════════════════════════════════════════════════════════════════════════════

class TestEvaluateQuiz:

    def test_all_correct(self, sample_questions):
        answers = {0: "B", 1: "C", 2: "B"}
        result = evaluate_quiz(sample_questions, answers, "E001")
        assert result.score == 3
        assert result.total == 3
        assert result.pct == 100.0

    def test_all_wrong(self, sample_questions):
        answers = {0: "A", 1: "A", 2: "A"}
        result = evaluate_quiz(sample_questions, answers, "E002")
        assert result.score == 0
        assert result.pct == 0.0

    def test_partial_correct(self, sample_questions):
        answers = {0: "B", 1: "A", 2: "B"}
        result = evaluate_quiz(sample_questions, answers, "E003")
        assert result.score == 2
        assert result.pct == pytest.approx(66.7, rel=0.1)

    def test_missing_answers(self, sample_questions):
        answers = {0: "B"}  # only answered q0
        result = evaluate_quiz(sample_questions, answers, "E004")
        assert result.score == 1
        assert result.total == 3
        assert len(result.details) == 3

    def test_no_questions(self):
        result = evaluate_quiz([], {}, "E005")
        assert result.score == 0
        assert result.total == 0
        assert result.pct == 0.0

    def test_detail_breakdown(self, sample_questions):
        answers = {0: "B", 1: "A", 2: "B"}
        result = evaluate_quiz(sample_questions, answers, "E001")
        assert len(result.details) == 3
        assert result.details[0]["is_correct"] is True
        assert result.details[1]["is_correct"] is False
        assert result.details[1]["correct_answer"] == "C"
        assert result.details[1]["submitted_answer"] == "A"

    def test_case_insensitive_answers(self, sample_questions):
        answers = {0: "b", 1: "c", 2: "b"}
        result = evaluate_quiz(sample_questions, answers, "E006")
        assert result.score == 3
