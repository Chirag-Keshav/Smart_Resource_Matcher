"""
test_matcher.py
---------------
Unit tests for the Phase 3 Employee Matcher & Ranker.

Tests cover:
  - skill_matcher.match_employees()
  - ranking.rank_employees()

Uses small fixture DataFrames to assert correct match counts,
matched skill sets, ranking order, and edge cases.
"""

import pandas as pd
import pytest

from src.matcher.skill_matcher import match_employees
from src.matcher.ranking import rank_employees


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def employees_df() -> pd.DataFrame:
    """
    Small fixture DataFrame mimicking the output of ``loader.load_employees()``.
    """
    return pd.DataFrame({
        "employee_id": ["E001", "E002", "E003", "E004", "E005"],
        "name": ["Alice", "Bob", "Carol", "Dave", "Eve"],
        "department": ["AI", "Backend", "Data", "Frontend", "AI"],
        "designation": [
            "ML Engineer", "Software Engineer",
            "Data Analyst", "Frontend Dev", "Research Scientist",
        ],
        "skills": [
            "Python, PyTorch, NLP, Pandas",
            "Python, Java, SQL, Docker",
            "SQL, Excel, Tableau, Pandas",
            "JavaScript, React, CSS, HTML",
            "Python, PyTorch, TensorFlow, NLP, Computer Vision",
        ],
        "skills_list": [
            ["python", "pytorch", "nlp", "pandas"],
            ["python", "java", "sql", "docker"],
            ["sql", "excel", "tableau", "pandas"],
            ["javascript", "react", "css", "html"],
            ["python", "pytorch", "tensorflow", "nlp", "computer vision"],
        ],
        "experience_years": [5.0, 8.0, 3.0, 2.0, 10.0],
    })


# ═══════════════════════════════════════════════════════════════════════════════
# Tests — match_employees()
# ═══════════════════════════════════════════════════════════════════════════════

class TestMatchEmployees:
    """Tests for skill_matcher.match_employees()."""

    def test_basic_matching(self, employees_df):
        """Resume with Python & SQL should match E001, E002, E003, E005."""
        result = match_employees(["python", "sql"], employees_df)

        assert len(result) == 4
        matched_ids = set(result["employee_id"])
        assert matched_ids == {"E001", "E002", "E003", "E005"}

    def test_match_count_correct(self, employees_df):
        """Verify match_count reflects the actual number of overlapping skills."""
        result = match_employees(["python", "pytorch", "nlp"], employees_df)

        # E001 has python, pytorch, nlp → 3
        e001 = result[result["employee_id"] == "E001"]
        assert e001.iloc[0]["match_count"] == 3

        # E002 has python only → 1
        e002 = result[result["employee_id"] == "E002"]
        assert e002.iloc[0]["match_count"] == 1

        # E005 has python, pytorch, nlp → 3
        e005 = result[result["employee_id"] == "E005"]
        assert e005.iloc[0]["match_count"] == 3

    def test_matched_skills_content(self, employees_df):
        """matched_skills column should contain the actual intersecting skill names."""
        result = match_employees(["python", "pandas"], employees_df)

        e001 = result[result["employee_id"] == "E001"]
        assert set(e001.iloc[0]["matched_skills"]) == {"python", "pandas"}

        e003 = result[result["employee_id"] == "E003"]
        assert set(e003.iloc[0]["matched_skills"]) == {"pandas"}

    def test_no_matches(self, employees_df):
        """Skills with zero overlap should return an empty DataFrame."""
        result = match_employees(["rust", "go", "elixir"], employees_df)
        assert result.empty

    def test_empty_resume_skills(self, employees_df):
        """An empty skill list should return an empty DataFrame."""
        result = match_employees([], employees_df)
        assert result.empty

    def test_case_insensitive(self, employees_df):
        """Resume skills in mixed case should still match (normalised to lowercase)."""
        result = match_employees(["PYTHON", "Pandas"], employees_df)

        assert len(result) > 0
        assert "E001" in result["employee_id"].values

    def test_whitespace_handling(self, employees_df):
        """Leading/trailing whitespace in resume skills should be stripped."""
        result = match_employees(["  python  ", " sql"], employees_df)

        assert len(result) > 0
        assert "E002" in result["employee_id"].values

    def test_missing_skills_list_column(self):
        """Should raise ValueError if the DataFrame lacks skills_list."""
        bad_df = pd.DataFrame({"employee_id": ["E001"], "name": ["Alice"]})

        with pytest.raises(ValueError, match="skills_list"):
            match_employees(["python"], bad_df)

    def test_does_not_mutate_input(self, employees_df):
        """match_employees should not modify the original DataFrame."""
        original_cols = set(employees_df.columns)
        match_employees(["python"], employees_df)
        assert set(employees_df.columns) == original_cols
        assert "matched_skills" not in employees_df.columns


# ═══════════════════════════════════════════════════════════════════════════════
# Tests — rank_employees()
# ═══════════════════════════════════════════════════════════════════════════════

class TestRankEmployees:
    """Tests for ranking.rank_employees()."""

    def test_ranking_order(self, employees_df):
        """Higher match_count + higher experience should rank first."""
        matched = match_employees(["python", "pytorch", "nlp"], employees_df)
        ranked = rank_employees(matched, top_n=5)

        # E005 (3 matches, 10yr) and E001 (3 matches, 5yr) should be top-2
        assert ranked.iloc[0]["employee_id"] in {"E005", "E001"}
        # E005 should beat E001 due to higher experience
        assert ranked.iloc[0]["employee_id"] == "E005"
        assert ranked.iloc[1]["employee_id"] == "E001"

    def test_top_n_limits_results(self, employees_df):
        """top_n should cap the number of returned employees."""
        matched = match_employees(["python", "sql"], employees_df)
        ranked = rank_employees(matched, top_n=2)

        assert len(ranked) == 2

    def test_score_column_exists(self, employees_df):
        """The output should have a 'score' column."""
        matched = match_employees(["python"], employees_df)
        ranked = rank_employees(matched)

        assert "score" in ranked.columns
        assert ranked["score"].dtype == float

    def test_scores_descending(self, employees_df):
        """Scores should be in descending order."""
        matched = match_employees(["python", "pytorch", "nlp"], employees_df)
        ranked = rank_employees(matched, top_n=10)

        scores = ranked["score"].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_empty_input(self, employees_df):
        """Ranking an empty DataFrame should return an empty DataFrame."""
        matched = match_employees(["rust"], employees_df)  # no matches
        ranked = rank_employees(matched)

        assert ranked.empty

    def test_single_employee(self):
        """Ranking should work with just one employee."""
        df = pd.DataFrame({
            "employee_id": ["E001"],
            "name": ["Alice"],
            "skills_list": [["python"]],
            "match_count": [1],
            "matched_skills": [["python"]],
            "experience_years": [5.0],
        })
        ranked = rank_employees(df, top_n=5)

        assert len(ranked) == 1
        assert ranked.iloc[0]["score"] > 0

    def test_equal_experience_scoring(self):
        """When all employees have the same experience, normalised_experience = 1.0."""
        df = pd.DataFrame({
            "employee_id": ["E001", "E002"],
            "name": ["Alice", "Bob"],
            "skills_list": [["python", "sql"], ["python"]],
            "match_count": [2, 1],
            "matched_skills": [["python", "sql"], ["python"]],
            "experience_years": [5.0, 5.0],
        })
        ranked = rank_employees(df, top_n=5)

        # E001 should rank higher (2 matches vs 1, same experience)
        assert ranked.iloc[0]["employee_id"] == "E001"

    def test_missing_columns_raises(self):
        """Should raise ValueError for missing required columns."""
        bad_df = pd.DataFrame({"employee_id": ["E001"]})

        with pytest.raises(ValueError, match="missing required columns"):
            rank_employees(bad_df)

    def test_top_n_larger_than_data(self, employees_df):
        """If top_n > number of matched employees, return all of them."""
        matched = match_employees(["python"], employees_df)
        ranked = rank_employees(matched, top_n=100)

        assert len(ranked) == len(matched)
