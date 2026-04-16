"""
ranking.py
----------
Ranks matched employees by a weighted score that blends skill-match
count with years of experience.
"""

import pandas as pd

from src.config.settings import (
    DEFAULT_TOP_N,
    MATCH_WEIGHT,
    EXPERIENCE_WEIGHT,
)


def rank_employees(
    matched_df: pd.DataFrame,
    top_n: int = DEFAULT_TOP_N,
) -> pd.DataFrame:
    """
    Score and rank employees who were matched by :func:`skill_matcher.match_employees`.

    Scoring formula::

        score = match_count × MATCH_WEIGHT + normalised_experience × EXPERIENCE_WEIGHT

    ``normalised_experience`` maps each employee's ``experience_years`` to
    ``[0, max_experience]`` → ``[0, 1]`` via min-max scaling (or 0 when
    all employees share the same experience value).

    Parameters
    ----------
    matched_df : pd.DataFrame
        Output of ``match_employees()`` — must include ``match_count``
        and ``experience_years`` columns.
    top_n : int, optional
        How many employees to return.  Defaults to
        ``settings.DEFAULT_TOP_N`` (10).

    Returns
    -------
    pd.DataFrame
        The top-N employees sorted by ``score`` descending, with the
        ``score`` column appended.

    Raises
    ------
    ValueError
        If required columns are missing.
    """
    required = {"match_count", "experience_years"}
    missing = required - set(matched_df.columns)
    if missing:
        raise ValueError(
            f"matched_df is missing required columns: {missing}. "
            "Ensure you pass the output of match_employees()."
        )

    if matched_df.empty:
        result = matched_df.copy()
        result["score"] = pd.Series(dtype=float)
        return result

    df = matched_df.copy()

    # ── Normalise experience to [0, 1] ────────────────────────────────────
    exp = df["experience_years"].astype(float)
    exp_min, exp_max = exp.min(), exp.max()

    if exp_max == exp_min:
        # All employees have the same experience — treat as 1.0 (everyone equal)
        df["normalised_experience"] = 1.0
    else:
        df["normalised_experience"] = (exp - exp_min) / (exp_max - exp_min)

    # ── Compute weighted score ────────────────────────────────────────────
    df["score"] = (
        df["match_count"] * MATCH_WEIGHT
        + df["normalised_experience"] * EXPERIENCE_WEIGHT
    )

    # ── Sort and trim ─────────────────────────────────────────────────────
    df = df.sort_values("score", ascending=False).head(top_n).reset_index(drop=True)

    # Drop intermediate column; keep clean output
    df = df.drop(columns=["normalised_experience"])

    return df
