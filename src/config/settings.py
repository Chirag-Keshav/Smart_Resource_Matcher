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

# ── Quiz / Groq (Phase 6) ────────────────────────────────────────────────────
import os
from dotenv import load_dotenv
# Set override=True so the .env file crushes the global ~/.zshrc variable
load_dotenv(override=True)
load_dotenv(PROJECT_ROOT / ".env")

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL:   str = "llama-3.3-70b-versatile"
QUIZ_MIN_Q:   int = 5
QUIZ_MAX_Q:   int = 10

