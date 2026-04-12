"""
loader.py
---------
Data loading module for the Smart Resource Matcher project.

Provides clean, typed DataFrames for employees and schedules
from the raw CSV datasets.
"""

import pandas as pd
from pathlib import Path
from typing import Optional

from src.config.settings import EMPLOYEES_CSV, SCHEDULES_CSV
from src.utils.text_utils import tokenize_skills


def load_employees(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load and clean the employees dataset.

    Parameters
    ----------
    path : Path, optional
        Override CSV path (useful in tests).  Defaults to
        ``settings.EMPLOYEES_CSV``.

    Returns
    -------
    pd.DataFrame
        Columns:
        - ``employee_id``      (str)
        - ``name``             (str)
        - ``department``       (str)
        - ``designation``      (str)
        - ``skills``           (str)  — original comma-separated string
        - ``skills_list``      (list) — parsed & normalised skill list
        - ``experience_years`` (float)
    """
    csv_path = path or EMPLOYEES_CSV
    df = pd.read_csv(csv_path, dtype=str)

    # Normalise column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Required columns existence check
    required = {"employee_id", "name", "department", "designation", "skills", "experience_years"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"employees CSV is missing columns: {missing}")

    # Clean strings
    for col in ["employee_id", "name", "department", "designation", "skills"]:
        df[col] = df[col].fillna("").str.strip()

    # Parse experience to numeric
    df["experience_years"] = pd.to_numeric(df["experience_years"], errors="coerce").fillna(0.0)

    # Add parsed skills list column
    df["skills_list"] = df["skills"].apply(tokenize_skills)

    return df.reset_index(drop=True)


def load_schedules(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load and clean the employee meeting schedules dataset.

    Parameters
    ----------
    path : Path, optional
        Override CSV path (useful in tests).  Defaults to
        ``settings.SCHEDULES_CSV``.

    Returns
    -------
    pd.DataFrame
        Columns:
        - ``employee_id``    (str)
        - ``date``           (datetime.date via pd.Timestamp)
        - ``start_time``     (str, HH:MM)
        - ``end_time``       (str, HH:MM)
        - ``meeting_title``  (str)
    """
    csv_path = path or SCHEDULES_CSV
    df = pd.read_csv(csv_path, dtype=str)

    # Normalise column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    required = {"employee_id", "date", "start_time", "end_time"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"schedules CSV is missing columns: {missing}")

    # Clean strings
    for col in ["employee_id", "start_time", "end_time"]:
        df[col] = df[col].fillna("").str.strip()

    if "meeting_title" not in df.columns:
        df["meeting_title"] = "Meeting"
    df["meeting_title"] = df["meeting_title"].fillna("Meeting").str.strip()

    # Parse date column
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

    # Drop rows with unparseable dates or missing employee ids
    df = df.dropna(subset=["date"]).reset_index(drop=True)
    df = df[df["employee_id"] != ""].reset_index(drop=True)

    return df
