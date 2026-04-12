"""
settings.py
-----------
Central configuration for the Smart Resource Matcher project.
All path and constant references should import from here.
"""

from pathlib import Path

# ── Project root ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # Smart_Resource_Matcher/

# ── Data paths ────────────────────────────────────────────────────────────────
DATA_DIR          = PROJECT_ROOT / "data"
RAW_DATA_DIR      = DATA_DIR / "raw"
PROCESSED_DIR     = DATA_DIR / "processed"

EMPLOYEES_CSV     = RAW_DATA_DIR / "employees.csv"
SCHEDULES_CSV     = RAW_DATA_DIR / "schedules.csv"

# ── Working hours (24-hour strings) ───────────────────────────────────────────
WORK_START: str = "09:00"
WORK_END:   str = "18:00"

# ── Matching & ranking defaults ───────────────────────────────────────────────
DEFAULT_TOP_N:          int   = 10      # How many employees to return
MATCH_WEIGHT:           float = 0.6    # Weight for skill-match count in score
EXPERIENCE_WEIGHT:      float = 0.4    # Weight for experience in score

# ── Scheduler defaults ────────────────────────────────────────────────────────
DEFAULT_SLOT_DURATION:  int = 60       # Free-slot size in minutes

# ── Resume upload directory ───────────────────────────────────────────────────
RESUME_DIR = PROJECT_ROOT / "resumes"
