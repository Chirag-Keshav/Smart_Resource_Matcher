"""
text_utils.py
-------------
Utilities for normalising and tokenising skill strings.
"""

import re
from typing import List, Set


def normalize_skill(skill: str) -> str:
    """
    Lowercase and strip a skill string.

    Examples
    --------
    >>> normalize_skill("  Python ")
    'python'
    >>> normalize_skill("Machine Learning")
    'machine learning'
    """
    return skill.strip().lower()


def tokenize_skills(raw: str) -> List[str]:
    """
    Parse a comma-separated skill string into a list of normalised skills.

    Parameters
    ----------
    raw : str
        Raw skill string, e.g. ``"Python, SQL, Scikit-learn"``.

    Returns
    -------
    List[str]
        Normalised list, e.g. ``["python", "sql", "scikit-learn"]``.
    """
    if not raw or not isinstance(raw, str):
        return []
    return [normalize_skill(s) for s in raw.split(",") if s.strip()]


def build_skill_vocabulary(skills_series) -> Set[str]:
    """
    Build a flat set of all unique normalised skills from a pandas Series
    where each element is a comma-separated skill string.

    Parameters
    ----------
    skills_series : pd.Series
        The ``skills`` column from the employees DataFrame.

    Returns
    -------
    Set[str]
        All unique normalised skill tokens across all employees.
    """
    vocab: Set[str] = set()
    for raw in skills_series.dropna():
        vocab.update(tokenize_skills(str(raw)))
    return vocab
