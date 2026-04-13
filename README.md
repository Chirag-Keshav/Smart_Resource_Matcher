# 🧠 Smart Resource Matcher

> **Intelligently match the right people to the right tasks — based on skills, experience, real-time availability, and now an AI-powered readiness quiz.**

Smart Resource Matcher is a Python-based tool that helps teams and project managers find the best-fit employees for a given set of required skills. It parses resumes, scores candidates using a weighted ranking algorithm, checks calendar schedules for availability, and — as a final phase — generates a tailored MCQ quiz via Groq's free LLM API to prepare the employee and give the employer an extra layer of confidence.

---

## ✨ Features

- **Skill-Based Matching** — Tokenises and normalises skill strings, then finds employees whose skill sets best align with the requirements.
- **Weighted Ranking** — Scores candidates using a configurable blend of skill-match count (60 %) and years of experience (40 %).
- **Availability Scheduling** — Computes free time slots within a working day (09:00–18:00) by merging booked meeting intervals from schedule data.
- **Resume Parsing** — Extracts skills from uploaded PDF/DOCX résumés (powered by PyMuPDF and python-docx).
- **AI Quiz Generator** — Generates 5–10 MCQs based on the matched skills and job context using Groq's free LLM API. Scored instantly, with per-question feedback.
- **REST API** — FastAPI backend for programmatic access and integration with other systems.
- **Interactive UI** — Streamlit front-end with tabs: Resume Upload → Matched Employees → Availability → Skill Quiz.
- **Configurable** — All paths, weights, and defaults live in a single `settings.py`.

---

## 🏗️ Project Structure

```
Smart_Resource_Matcher/
├── api/
│   └── app.py                    # FastAPI application
├── data/
│   ├── raw/
│   │   ├── employees.csv         # Employee profiles (id, name, dept, skills, experience)
│   │   └── schedules.csv         # Meeting schedules (employee_id, date, start, end)
│   └── processed/                # Cleaned / intermediate data
├── notebooks/                    # Exploratory Jupyter notebooks
├── resumes/                      # Uploaded résumé files (PDF / DOCX)
├── src/
│   ├── config/
│   │   └── settings.py           # Central config (paths, weights, Groq, quiz defaults)
│   ├── data_loader/
│   │   └── loader.py             # CSV loaders → typed DataFrames
│   ├── matcher/
│   │   ├── skill_matcher.py      # Skill overlap logic
│   │   └── ranking.py            # Weighted scoring & top-N selection
│   ├── resume_parser/
│   │   ├── parser.py             # PDF/DOCX text extraction
│   │   └── skill_extractor.py    # Skill identification from raw text
│   ├── scheduler/
│   │   └── availability.py       # Free-slot computation per employee
│   ├── quiz/                     # Phase 6 — AI Quiz Generator
│   │   ├── __init__.py
│   │   ├── models.py             # QuizQuestion & QuizResult dataclasses
│   │   ├── generator.py          # Groq API call, prompt engineering, JSON parse
│   │   └── evaluator.py          # Score computation & per-question feedback
│   ├── utils/
│   │   ├── text_utils.py         # Skill normalisation & tokenisation
│   │   └── time_utils.py         # Time parsing & free-slot algorithm
│   └── main.py                   # CLI / Streamlit entry point
├── tests/                        # Pytest test suite
│   └── test_quiz.py              # Mocked unit tests for Phase 6
│   └── test_matcher.py           # Mocked unit test for Matching sequence
│   └── test_scheduler.py         # Mocked unit test for scheduling sequence
├── .env                          # Template: GROQ_API_KEY
├── requirement.txt               # Python dependencies
└── README.md
```

---

## ⚙️ Configuration

All tuneable settings are in [`src/config/settings.py`](src/config/settings.py):

| Setting | Default | Description |
|---|---|---|
| `WORK_START` / `WORK_END` | `"09:00"` / `"18:00"` | Working-day boundaries |
| `DEFAULT_TOP_N` | `10` | Number of candidates returned |
| `MATCH_WEIGHT` | `0.6` | Weight of skill-match score |
| `EXPERIENCE_WEIGHT` | `0.4` | Weight of experience score |
| `DEFAULT_SLOT_DURATION` | `60` min | Minimum free-slot length |
| `GROQ_MODEL` | `"llama-3.3-70b-versatile"` | Groq model for quiz generation |
| `QUIZ_MIN_Q` / `QUIZ_MAX_Q` | `5` / `10` | Question count bounds |

The `GROQ_API_KEY` is read from the environment (or a `.env` file via `python-dotenv`).

---

## 🚀 Getting Started

### Prerequisites

- Python ≥ 3.10
- A virtual environment (recommended)
- A free [Groq API key](https://console.groq.com/) *(only required for Phase 6 quiz feature)*

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/Smart_Resource_Matcher.git
cd Smart_Resource_Matcher

# 2. Create & activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirement.txt

# 4. (Optional) Set up Groq API key for the quiz feature
cp .env.example .env
# Edit .env and add: GROQ_API_KEY=your_key_here
```

### Data Setup

Place your input CSVs in `data/raw/`:

**`employees.csv`** — required columns:
```
employee_id, name, department, designation, skills, experience_years
```
> `skills` should be a comma-separated string, e.g. `"Python, SQL, Scikit-learn"`.

**`schedules.csv`** — required columns:
```
employee_id, date, start_time, end_time[, meeting_title]
```
> `date` format: `YYYY-MM-DD`. Times: `HH:MM`.

---

## 🖥️ Usage

### CLI

```bash
python -m src.main
```

### Streamlit UI

```bash
streamlit run src/main.py
```

The UI has four tabs:

| Tab | Description |
|---|---|
| 📄 Resume Upload | Upload a PDF/DOCX résumé and extract skills |
| 👥 Matched Employees | View ranked employee matches with scores |
| 📅 Availability | See free time slots for top matches on a target date |
| 📝 Skill Quiz | Generate and take an AI-powered MCQ quiz |

### REST API

```bash
uvicorn api.app:app --reload
```

API docs available at `http://127.0.0.1:8000/docs`.

Key endpoints:

| Method | Path | Description |
|---|---|---|
| `POST` | `/analyze` | Upload resume → matched employees |
| `GET` | `/employees` | List all employees |
| `GET` | `/availability/{employee_id}` | Free slots for an employee |
| `POST` | `/quiz/generate` | Generate MCQ quiz from skills |
| `POST` | `/quiz/submit` | Submit answers → score & feedback |

---

## 🤖 AI Quiz Feature (Phase 6)

The quiz generator sends only the **skills list** and an optional job context sentence to Groq — no personal data (names or IDs) is transmitted.

The quiz is **optional and gracefully degraded**: if `GROQ_API_KEY` is not set, the quiz tab displays a clear notice and all other functionality remains unaffected.

**Groq free-tier limits** (as of 2026): 30 requests/min, 14,400 requests/day — well above typical usage.

---

## 🧪 Running Tests

```bash
pytest tests/
```

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `pandas` | DataFrame handling for employee & schedule data |
| `pymupdf` | PDF text extraction for resume parsing |
| `python-docx` | DOCX text extraction for resume parsing |
| `streamlit` | Interactive web UI |
| `fastapi` + `uvicorn` | REST API server |
| `groq` | Official Groq SDK for LLM quiz generation |
| `python-dotenv` | Load `GROQ_API_KEY` from `.env` file |
| `pytest` | Testing framework |

---

## 🤝 Contributing

1. Fork the repo and create a feature branch: `git checkout -b feat/my-feature`
2. Make your changes and add tests under `tests/`
3. Run `pytest` and ensure all tests pass
4. Open a pull request with a clear description of your changes

---

## 📄 License

This project is licensed under the MIT License.
