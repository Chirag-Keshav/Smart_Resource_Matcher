"""
skill_matcher.py
----------------
Matches employees to a set of resume-extracted skills by computing
the intersection between the candidate's skills and each employee's
skill set.
"""

from typing import List

import pandas as pd

from src.utils.text_utils import normalize_skill


def match_employees(
    resume_skills: List[str],
    employees_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Match employees against a list of extracted resume skills.

    For each employee, computes the intersection of their ``skills_list``
    with the (normalised) resume skills.  Only employees with at least
    one overlapping skill are returned.

    Parameters
    ----------
    resume_skills : List[str]
        Skills extracted from a candidate's resume (already normalised
        or will be normalised here).
    employees_df : pd.DataFrame
        Must contain the ``skills_list`` column (list of normalised skills),
        as produced by ``loader.load_employees()``.

    Returns
    -------
    pd.DataFrame
        A *copy* of the input DataFrame filtered to employees with ≥ 1
        match, enriched with two new columns:

        - ``matched_skills`` (list[str]) — the overlapping skills
        - ``match_count``    (int)       — len(matched_skills)

    Raises
    ------
    ValueError
        If ``employees_df`` does not contain a ``skills_list`` column.
    """
    if "skills_list" not in employees_df.columns:
        raise ValueError(
            "employees_df must contain a 'skills_list' column. "
            "Use loader.load_employees() to produce the expected schema."
        )

    # Normalise the incoming resume skills into a set for O(1) lookups
    resume_set = {normalize_skill(s) for s in resume_skills if s.strip()}

    if not resume_set:
        # No skills provided → no matches possible
        result = employees_df.head(0).copy()
        result["matched_skills"] = pd.Series(dtype=object)
        result["match_count"] = pd.Series(dtype=int)
        return result

    # Compute intersection per employee
    df = employees_df.copy()
    df["matched_skills"] = df["skills_list"].apply(
        lambda emp_skills: sorted(resume_set & set(emp_skills))
    )
    df["match_count"] = df["matched_skills"].apply(len)

    # Filter out employees with zero matches
    df = df[df["match_count"] > 0].reset_index(drop=True)

    return df
