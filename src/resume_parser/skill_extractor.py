"""
skill_extractor.py
------------------
Extract technical skills from raw resume text using vocabulary-based
keyword matching.

The vocabulary is built from the unique skills present in the employee
dataset (``employees.csv``), ensuring that extracted resume skills live
in the same namespace as the employee skills — which makes downstream
matching deterministic and consistent.

An **alias map** expands common abbreviations and synonyms so that,
for example, ``"ML"`` in a resume is resolved to ``"machine learning"``.
"""

import re
from typing import List, Set

from src.utils.text_utils import normalize_skill


# ── Alias map ─────────────────────────────────────────────────────────────────
# Keys are normalised aliases; values are the canonical skill name
# (which must exist in the employee vocabulary).
# Extend this map as new abbreviations are encountered.

SKILL_ALIASES: dict[str, str] = {
    # AI / ML
    "ml":                   "machine learning",
    "deep learning":        "pytorch",          # closest vocab match
    "dl":                   "pytorch",
    "natural language processing": "nlp",
    "cv":                   "computer vision",
    "sklearn":              "scikit-learn",
    "sk-learn":             "scikit-learn",
    "sci-kit learn":        "scikit-learn",
    "tf":                   "tensorflow",

    # Web / Programming
    "js":                   "javascript",
    "es6":                  "javascript",
    "typescript":           "javascript",
    "ts":                   "javascript",
    "reactjs":              "react",
    "react.js":             "react",
    "nodejs":               "node.js",
    "node":                 "node.js",
    "express":              "node.js",
    "expressjs":            "node.js",
    "html5":                "html",
    "css3":                 "css",
    "tailwind":             "css",
    "bootstrap":            "css",
    "spring boot":          "spring",
    "springboot":           "spring",

    # Data
    "mysql":                "sql",
    "postgresql":           "sql",
    "postgres":             "sql",
    "sqlite":               "sql",
    "mongodb":              "sql",          # maps to closest DB skill in vocab

    # DevOps
    "amazon web services":  "aws",
    "cicd":                 "ci/cd",
    "ci cd":                "ci/cd",
    "continuous integration": "ci/cd",
    "k8s":                  "kubernetes",
    "containerization":     "docker",
}


# ── Skill extraction ─────────────────────────────────────────────────────────

def _build_patterns(vocab: Set[str]) -> list[tuple[re.Pattern, str]]:
    """
    Pre-compile regex patterns for each vocabulary token and alias.

    Each pattern uses word-boundary matching (``\\b``) so that e.g.
    ``"sql"`` does not accidentally match inside ``"postgresql"``
    (the alias map handles that separately).

    Returns a list of ``(compiled_pattern, canonical_skill)`` tuples,
    sorted longest-first so multi-word skills match before their substrings.
    """
    # Merge vocab + aliases into a single lookup:  pattern_text → canonical
    lookup: dict[str, str] = {}

    for skill in vocab:
        lookup[skill] = skill

    for alias, canonical in SKILL_ALIASES.items():
        if canonical in vocab:
            lookup[alias] = canonical

    # Sort longest-first to prefer multi-word matches
    patterns: list[tuple[re.Pattern, str]] = []
    for text in sorted(lookup, key=len, reverse=True):
        escaped = re.escape(text)
        pat = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
        patterns.append((pat, lookup[text]))

    return patterns


def extract_skills(text: str, vocab: Set[str]) -> List[str]:
    """
    Extract skills from resume text by matching against a known vocabulary.

    Parameters
    ----------
    text : str
        Raw text extracted from a resume (PDF / DOCX).
    vocab : Set[str]
        Set of normalised skill strings (typically built via
        :func:`src.utils.text_utils.build_skill_vocabulary`).

    Returns
    -------
    List[str]
        De-duplicated list of matched canonical skill names,
        sorted alphabetically.

    Examples
    --------
    >>> vocab = {"python", "sql", "react", "machine learning", "nlp"}
    >>> text = "Proficient in Python, ML, and React development."
    >>> extract_skills(text, vocab)
    ['machine learning', 'python', 'react']
    """
    if not text or not vocab:
        return []

    patterns = _build_patterns(vocab)
    found: Set[str] = set()

    for pat, canonical in patterns:
        if pat.search(text):
            found.add(canonical)

    return sorted(found)
