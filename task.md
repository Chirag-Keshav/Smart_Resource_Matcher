# Smart Resource Matcher — Task Tracker

## Phase 1 — Foundation ✅
- [x] `src/config/settings.py` — paths, working hours, weights, defaults
- [x] `src/utils/text_utils.py` — `normalize_skill`, `tokenize_skills`, `build_skill_vocabulary`
- [x] `src/utils/time_utils.py` — `parse_time`, `get_free_slots`
- [x] `src/data_loader/loader.py` — `load_employees`, `load_schedules`
- [x] `__init__.py` files for all packages (src, config, data_loader, utils, matcher, resume_parser, scheduler, tests)
- [x] `requirement.txt` updated
- [x] `.venv` created with all deps installed
- [x] Smoke test passed — 200 employees, 882 schedules, vocab=19 skills, free-slot logic verified
- [x] Notion: Implementation plan recorded under Study/Projects/Smart Resource Matcher

## Phase 2 — Resume Parser & Skill Extractor
- [ ] `src/resume_parser/parser.py` — `extract_text_from_pdf`, `extract_text_from_docx`, `extract_text` dispatch
- [ ] `src/resume_parser/skill_extractor.py` — vocab-based keyword matching + alias map, `extract_skills`
- [ ] Sample resume (PDF/DOCX) for manual testing

## Phase 3 — Employee Matcher & Ranker
- [ ] `src/matcher/skill_matcher.py` — `match_employees`
- [ ] `src/matcher/ranking.py` — `rank_employees` (weighted score)
- [ ] `tests/test_matcher.py` — pytest fixture tests

## Phase 4 — Availability Scheduler
- [ ] `src/scheduler/availability.py` — `get_availability`
- [ ] `tests/test_scheduler.py` — fully booked / partial / free day fixtures

## Phase 5 — Streamlit UI & FastAPI
- [ ] `src/main.py` — `run_pipeline` core orchestration function
- [ ] `app.py` — Streamlit UI (sidebar + 3 tabs)
- [ ] `api/app.py` — FastAPI REST layer
- [ ] End-to-end test via browser
