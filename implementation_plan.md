# Smart Resource Matcher — Implementation Plan

## Background

The project structure already exists with placeholder (empty) Python files and two pre-generated datasets:
- `data/raw/employees.csv` — 200 employees (employee_id, name, department, designation, skills, experience_years)
- `data/raw/schedules.csv` — ~882 meeting entries (employee_id, date, start_time, end_time, meeting_title)

All `src/`, `api/`, `tests/` files are empty. We will fill them in **4 phases**, each building on the last and being independently testable.

---

## Phase Breakdown

### Phase 1 — Foundation: Config, Data Loader & Utils
**Goal**: Set up shared infrastructure that every other module depends on.

#### [MODIFY] `src/config/settings.py`
- Paths to raw data files (employees.csv, schedules.csv)
- Working hours constants (`WORK_START = "09:00"`, `WORK_END = "18:00"`)
- Top-N results constants, slot duration defaults

#### [MODIFY] `src/data_loader/loader.py`
- `load_employees()` → returns a cleaned `pd.DataFrame`
- `load_schedules()` → returns a cleaned `pd.DataFrame`
- Handles parsing of the `skills` column (comma-separated string → Python list)

#### [MODIFY] `src/utils/text_utils.py`
- `normalize_skill(skill: str) → str` — lowercase, strip whitespace
- `tokenize_skills(raw: str) → List[str]` — parse comma-separated skill strings

#### [MODIFY] `src/utils/time_utils.py`
- `parse_time(s: str) → datetime.time`
- `get_free_slots(meetings, work_start, work_end, slot_duration) → List[tuple]`

**Tests**: No dedicated test file for phase 1; tested implicitly in later phases. We'll add a quick smoke test in the loader.

---

### Phase 2 — Resume Parser & Skill Extractor
**Goal**: Accept a PDF or DOCX resume and return a list of extracted technical skills.

#### [MODIFY] `src/resume_parser/parser.py`
- `extract_text_from_pdf(path) → str` — uses `PyMuPDF` (fitz)
- `extract_text_from_docx(path) → str` — uses `python-docx`
- `extract_text(path) → str` — dispatch by file extension

#### [MODIFY] `src/resume_parser/skill_extractor.py`
- Maintains a **curated skills vocabulary** built from all unique skills in `employees.csv` — this ensures resume skills and employee skills share the same vocabulary space
- `extract_skills(text: str, vocab: Set[str]) → List[str]` — keyword matching with normalization; plus a small expandable alias map (e.g. `"ml" → "machine learning"`)

**Libraries**: `PyMuPDF` (fitz), `python-docx`

**Tests** (no new test file for phase 2; tested via Phase 3 integration):
- A sample minimal PDF/DOCX will be used for integration smoke testing.

---

### Phase 3 — Employee Matcher & Ranker
**Goal**: Given extracted skills → rank employees by match quality.

#### [MODIFY] `src/matcher/skill_matcher.py`
- `match_employees(resume_skills: List[str], employees_df: pd.DataFrame) → pd.DataFrame`
  - Computes `matched_skills` (intersection) and `match_count` per employee
  - Returns df filtered to employees with at least 1 match, enriched with `matched_skills` column

#### [MODIFY] `src/matcher/ranking.py`
- `rank_employees(matched_df: pd.DataFrame, top_n: int) → pd.DataFrame`
  - Scoring formula: `score = match_count * 0.6 + normalized_experience * 0.4`
  - Returns top-N sorted by score (desc)

**Tests**: `tests/test_matcher.py`
- Test with known skill list against a small fixture DataFrame
- Assert correct match counts and ranking order

---

### Phase 4 — Availability Scheduler
**Goal**: For a list of matched employees, find free time slots on a given date.

#### [MODIFY] `src/scheduler/availability.py`
- `get_availability(employee_ids, schedules_df, target_date, slot_duration=60) → Dict`
  - For each employee: filter their meetings on `target_date`, subtract booked ranges from 09:00–18:00, return free slots as list of `(start, end)` tuples

**Tests**: `tests/test_scheduler.py`
- Fixture schedules (fully booked day, partially free, completely free)
- Verify free slots are correctly computed

---

### Phase 5 — Streamlit UI & Main Entry Point
**Goal**: Wire everything into a polished, end-to-end Streamlit application.

#### [MODIFY] `src/main.py`
- Core pipeline function: `run_pipeline(resume_path, target_date, top_n, slot_duration) → dict`
- Callable from both the UI and CLI

#### [NEW] `app.py` (root level, Streamlit entry point)
- **Sidebar**: Date picker, Top-N slider, Slot duration selector
- **Main area** (tabbed):
  - Tab 1: Resume Upload → shows extracted skills as tags
  - Tab 2: Matched Employees → scored table with highlighted matching skills
  - Tab 3: Availability → per-employee free slot timeline calendar view

#### [MODIFY] `api/app.py`
- FastAPI app with endpoints:
  - `POST /analyze` — upload resume file, returns skills + matches + availability
  - `GET /employees` — list all employees
  - `GET /availability/{employee_id}` — get free slots for a given employee and date

---

## Tech Stack & Libraries

| Purpose | Library |
|---|---|
| PDF parsing | `PyMuPDF` (fitz) |
| DOCX parsing | `python-docx` |
| Data manipulation | `pandas` |
| Skill extraction | keyword matching + alias map |
| UI | `streamlit` |
| REST API | `fastapi` + `uvicorn` |
| Testing | `pytest` |

---

## Open Questions

> [!IMPORTANT]
> **Skill Extraction Approach**: The plan uses keyword/vocabulary matching (built from the employee dataset) for skill extraction. This is deterministic and fast. An NLP-based approach (e.g., spaCy NER, sentence-transformers for semantic matching) would be more robust but adds significant setup complexity. **Should we stick with keyword matching for now, or also include a semantic similarity fallback using sentence-transformers?**

> [!NOTE]
> **Phase Order**: I recommend we execute phases in order (1 → 2 → 3 → 4 → 5). Each phase is independently testable and produces a working increment. Please confirm, or let me know if you want a different order.

---

## Verification Plan

- **Phase 1**: `python -m pytest tests/` passes; `loader.py` can load both CSVs cleanly
- **Phase 2**: Manually test with a sample PDF/DOCX; extracted skills are visible
- **Phase 3**: `pytest tests/test_matcher.py` — all assertions pass
- **Phase 4**: `pytest tests/test_scheduler.py` — all assertions pass
- **Phase 5**: `streamlit run app.py` launches and the full flow works end-to-end
