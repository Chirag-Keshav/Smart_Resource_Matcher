# 🧠 Smart Resource Matcher

> **Intelligently match the right people to the right tasks — based on skills, experience, and real-time availability.**

Smart Resource Matcher is a Python-based tool that helps teams and project managers find the best-fit employees for a given set of required skills. It parses resumes, scores candidates using a weighted ranking algorithm, checks calendar schedules for availability, and exposes the results through both a REST API and an interactive Streamlit UI.

---

## ✨ Features

- **Skill-Based Matching** — Tokenises and normalises skill strings, then finds employees whose skill sets best align with the requirements.
- **Weighted Ranking** — Scores candidates using a configurable blend of skill-match count (60 %) and years of experience (40 %).
- **Availability Scheduling** — Computes free time slots within a working day (09:00–18:00) by merging booked meeting intervals from schedule data.
- **Resume Parsing** — Extracts skills from uploaded PDF/DOCX résumés (powered by PyMuPDF and python-docx).
- **REST API** — FastAPI backend (`api/app.py`) for programmatic access and integration with other systems.
- **Interactive UI** — Streamlit front-end for quick, no-code exploration.
- **Configurable** — All paths, weights, and defaults live in a single `settings.py`.

---

## 🏗️ Project Structure

```
Smart_Resource_Matcher/
├── api/
│   └── app.py                  # FastAPI application
├── data/
│   ├── raw/
│   │   ├── employees.csv       # Employee profiles (id, name, dept, skills, experience)
│   │   └── schedules.csv       # Meeting schedules (employee_id, date, start, end)
│   └── processed/              # Cleaned / intermediate data
├── notebooks/                  # Exploratory Jupyter notebooks
├── resumes/                    # Uploaded résumé files (PDF / DOCX)
├── src/
│   ├── config/
│   │   └── settings.py         # Central config (paths, weights, defaults)
│   ├── data_loader/
│   │   └── loader.py           # CSV loaders → typed DataFrames
│   ├── matcher/
│   │   ├── skill_matcher.py    # Skill overlap logic
│   │   └── ranking.py          # Weighted scoring & top-N selection
│   ├── resume_parser/
│   │   ├── parser.py           # PDF/DOCX text extraction
│   │   └── skill_extractor.py  # Skill identification from raw text
│   ├── scheduler/
│   │   └── availability.py     # Free-slot computation per employee
│   ├── utils/
│   │   ├── text_utils.py       # Skill normalisation & tokenisation
│   │   └── time_utils.py       # Time parsing & free-slot algorithm
│   └── main.py                 # CLI entry point
├── tests/                      # Pytest test suite
├── requirement.txt             # Python dependencies
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

---

## 🚀 Getting Started

### Prerequisites

- Python ≥ 3.10
- A virtual environment (recommended)

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

### REST API

```bash
uvicorn api.app:app --reload
```

API docs available at `http://127.0.0.1:8000/docs`.

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
