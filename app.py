"""
app.py — Streamlit UI for Smart Resource Matcher
=================================================
Launch with:  streamlit run app.py

Provides a polished four-tab interface:
  1. Resume Upload  → upload PDF/DOCX and view extracted skills
  2. Matched Employees → ranked table with scores and matched skills
  3. Availability   → per-employee free time-slot timeline
  4. Skill Quiz     → AI-generated MCQ quiz via Groq API
"""

import datetime
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config.settings import DEFAULT_TOP_N, DEFAULT_SLOT_DURATION
from src.main import run_pipeline

# ══════════════════════════════════════════════════════════════════════════════
# Page config & global styling
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Smart Resource Matcher",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for a polished, modern look
st.markdown("""
<style>
    /* ── Global ─────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Skill tags ────────────────────────────────────────────────── */
    .skill-tag {
        display: inline-block;
        padding: 5px 14px;
        margin: 4px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 500;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        letter-spacing: 0.3px;
    }
    .skill-tag-matched {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: #0a2e1a;
    }

    /* ── Timeline slot blocks ──────────────────────────────────────── */
    .slot-free {
        display: inline-block;
        padding: 6px 14px;
        margin: 3px;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 500;
        background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
        color: #0a2e1a;
    }
    .slot-none {
        display: inline-block;
        padding: 6px 14px;
        margin: 3px;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 500;
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        color: white;
    }

    /* ── Score badge ──────────────────────────────────────────────── */
    .score-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 700;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }

    /* ── Hero banner ──────────────────────────────────────────────── */
    .hero {
        text-align: center;
        padding: 30px 10px 15px;
    }
    .hero h1 {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .hero p {
        color: #888;
        font-size: 1rem;
        margin-top: 4px;
    }

    /* ── Section cards ───────────────────────────────────────────── */
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    .metric-card h3 {
        color: #667eea;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .metric-card .value {
        color: #f0f0f0;
        font-size: 1.8rem;
        font-weight: 700;
    }

    /* ── Streamlit table overrides ─────────────────────────────── */
    .stDataFrame td { font-size: 0.85rem; }
    .stDataFrame th { font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.5px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Sidebar
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.markdown("---")

    target_date = st.date_input(
        "📅 Target Date",
        value=datetime.date(2026, 4, 8),
        help="Check employee availability for this date",
    )
    top_n = st.slider(
        "🔢 Top-N Results",
        min_value=1,
        max_value=50,
        value=DEFAULT_TOP_N,
        help="Maximum number of matched employees to return",
    )
    slot_duration = st.select_slider(
        "⏱️ Slot Duration (min)",
        options=[15, 30, 45, 60, 90, 120],
        value=DEFAULT_SLOT_DURATION,
        help="Minimum free-slot length in minutes",
    )

    st.markdown("---")
    st.markdown(
        "<p style='color:#666; font-size:0.75rem; text-align:center;'>"
        "Smart Resource Matcher v1.0<br/>Built with Streamlit + FastAPI</p>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Hero
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(
    '<div class="hero">'
    '<h1>🎯 Smart Resource Matcher</h1>'
    '<p>Upload a resume → Find the best-matched employees → Check their availability</p>'
    '</div>',
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# Tabs
# ══════════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs([
    "📄 Resume Upload",
    "👥 Matched Employees",
    "🗓️ Availability",
    "🧠 Skill Quiz",
])


# ── Helper: render skill tags ────────────────────────────────────────────────

def _render_skill_tags(skills: list[str], css_class: str = "skill-tag") -> str:
    return " ".join(f'<span class="{css_class}">{s}</span>' for s in skills)


# ══════════════════════════════════════════════════════════════════════════════
# Tab 1 — Resume Upload
# ══════════════════════════════════════════════════════════════════════════════

with tab1:
    st.markdown("### 📄 Upload Resume")
    uploaded_file = st.file_uploader(
        "Drag and drop a PDF or DOCX resume",
        type=["pdf", "docx"],
        help="Supported formats: .pdf and .docx",
    )

    if uploaded_file is not None:
        # Save to temp file
        suffix = Path(uploaded_file.name).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name

        with st.spinner("🔍 Analysing resume…"):
            try:
                result = run_pipeline(
                    resume_path=tmp_path,
                    target_date=target_date,
                    top_n=top_n,
                    slot_duration=slot_duration,
                )
                # Store in session state for other tabs
                st.session_state["pipeline_result"] = result
                st.session_state["resume_name"] = uploaded_file.name
            except Exception as exc:
                st.error(f"❌ Error processing resume: {exc}")
                st.stop()
            finally:
                Path(tmp_path).unlink(missing_ok=True)

        # ── Metrics row ──────────────────────────────────────────────
        skills = result["extracted_skills"]
        matched_df = result["matched_employees"]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f'<div class="metric-card"><h3>Extracted Skills</h3>'
                f'<div class="value">{len(skills)}</div></div>',
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f'<div class="metric-card"><h3>Employees Matched</h3>'
                f'<div class="value">{len(matched_df)}</div></div>',
                unsafe_allow_html=True,
            )
        with col3:
            top_score = round(matched_df.iloc[0]["score"], 2) if not matched_df.empty else "—"
            st.markdown(
                f'<div class="metric-card"><h3>Top Score</h3>'
                f'<div class="value">{top_score}</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("### 🏷️ Extracted Skills")
        st.markdown(_render_skill_tags(skills), unsafe_allow_html=True)

    else:
        st.info("👆 Upload a resume to get started.")


# ══════════════════════════════════════════════════════════════════════════════
# Tab 2 — Matched Employees
# ══════════════════════════════════════════════════════════════════════════════

with tab2:
    if "pipeline_result" not in st.session_state:
        st.info("📄 Upload a resume in the first tab to see matched employees.")
    else:
        result = st.session_state["pipeline_result"]
        matched_df = result["matched_employees"]

        if matched_df.empty:
            st.warning("No employees matched the resume skills.")
        else:
            st.markdown(f"### 👥 Top {len(matched_df)} Matched Employees")
            st.markdown(
                f"*Resume: **{st.session_state.get('resume_name', 'unknown')}***"
            )

            # Build a display table
            display_rows = []
            for _, row in matched_df.iterrows():
                display_rows.append({
                    "Rank": len(display_rows) + 1,
                    "Employee ID": row["employee_id"],
                    "Name": row["name"],
                    "Department": row.get("department", ""),
                    "Designation": row.get("designation", ""),
                    "Experience (yr)": row["experience_years"],
                    "Match Count": row["match_count"],
                    "Score": round(float(row["score"]), 3),
                    "Matched Skills": ", ".join(row["matched_skills"]),
                })

            display_df = pd.DataFrame(display_rows)
            st.dataframe(
                display_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Rank": st.column_config.NumberColumn("🏆", width="small"),
                    "Score": st.column_config.ProgressColumn(
                        "Score",
                        min_value=0,
                        max_value=float(display_df["Score"].max()) * 1.1,
                        format="%.3f",
                    ),
                },
            )

            # Expandable skill detail per employee
            st.markdown("### 🔍 Skill Match Detail")
            for _, row in matched_df.iterrows():
                with st.expander(
                    f"**{row['name']}** ({row['employee_id']}) — "
                    f"{row['match_count']} skill{'s' if row['match_count'] != 1 else ''} matched"
                ):
                    st.markdown(
                        _render_skill_tags(row["matched_skills"], "skill-tag-matched"),
                        unsafe_allow_html=True,
                    )
                    st.caption(
                        f"Department: {row.get('department', '—')} · "
                        f"Designation: {row.get('designation', '—')} · "
                        f"Experience: {row['experience_years']} years"
                    )


# ══════════════════════════════════════════════════════════════════════════════
# Tab 3 — Availability
# ══════════════════════════════════════════════════════════════════════════════

with tab3:
    if "pipeline_result" not in st.session_state:
        st.info("📄 Upload a resume in the first tab to see availability.")
    else:
        result = st.session_state["pipeline_result"]
        matched_df = result["matched_employees"]
        avail = result["availability"]

        if matched_df.empty:
            st.warning("No matched employees to show availability for.")
        else:
            st.markdown(f"### 🗓️ Availability on **{target_date}**")
            st.caption(f"Showing free slots ≥ {slot_duration} min during 09:00–18:00")

            for _, row in matched_df.iterrows():
                emp_id = row["employee_id"]
                emp_name = row["name"]
                slots = avail.get(emp_id, [])

                st.markdown(f"**{emp_name}** (`{emp_id}`)")

                if slots:
                    slot_html = " ".join(
                        f'<span class="slot-free">'
                        f'{s.strftime("%H:%M")} – {e.strftime("%H:%M")}'
                        f'</span>'
                        for s, e in slots
                    )
                    st.markdown(slot_html, unsafe_allow_html=True)
                else:
                    st.markdown(
                        '<span class="slot-none">No available slots</span>',
                        unsafe_allow_html=True,
                    )

                st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# Tab 4 — Skill Quiz
# ══════════════════════════════════════════════════════════════════════════════

with tab4:
    if "pipeline_result" not in st.session_state:
        st.info("📄 Upload a resume in the first tab to generate a skill quiz.")
    else:
        result = st.session_state["pipeline_result"]
        extracted_skills = result["extracted_skills"]

        if not extracted_skills:
            st.warning("No skills were extracted from the resume.")
        else:
            st.markdown("### 🧠 AI-Powered Skill Quiz")
            st.caption(
                "Generate a tailored MCQ quiz based on the extracted skills. "
                "Powered by Groq (Llama 3.3 70B)."
            )

            # ── Quiz settings row ────────────────────────────────────
            col_ctx, col_n = st.columns([3, 1])
            with col_ctx:
                job_context = st.text_input(
                    "💼 Job Context (optional)",
                    placeholder="e.g. Senior backend engineer for fintech platform",
                    help="Brief job description for more relevant questions",
                )
            with col_n:
                n_questions = st.number_input(
                    "❓ Questions",
                    min_value=3,
                    max_value=10,
                    value=5,
                    step=1,
                )

            st.markdown("**Skills to test:** " + _render_skill_tags(extracted_skills), unsafe_allow_html=True)
            st.markdown("")

            # ── Generate quiz button ─────────────────────────────────
            if st.button("🚀 Generate Quiz", type="primary"):
                try:
                    from src.quiz.generator import generate_quiz

                    with st.spinner("🤖 Generating quiz via Groq AI…"):
                        questions = generate_quiz(
                            required_skills=extracted_skills,
                            job_context=job_context,
                            n_questions=int(n_questions),
                        )
                    st.session_state["quiz_questions"] = questions
                    st.session_state["quiz_submitted"] = False
                    st.rerun()

                except RuntimeError as exc:
                    st.error(f"⚠️ {exc}")
                    st.info(
                        "💡 Make sure `GROQ_API_KEY` is set in your `.env` file. "
                        "Get a free key at [console.groq.com](https://console.groq.com)"
                    )

            # ── Render quiz form ─────────────────────────────────────
            if "quiz_questions" in st.session_state and not st.session_state.get("quiz_submitted", False):
                questions = st.session_state["quiz_questions"]
                st.markdown("---")
                st.markdown(f"### 📝 Quiz ({len(questions)} questions)")

                with st.form("quiz_form"):
                    user_answers = {}
                    for i, q in enumerate(questions):
                        st.markdown(
                            f"**Q{i+1}.** {q.question}  "
                            f'<span class="skill-tag" style="font-size:0.7rem; padding:2px 8px;">{q.skill_tag}</span>',
                            unsafe_allow_html=True,
                        )
                        choice = st.radio(
                            f"Select answer for Q{i+1}",
                            options=q.options,
                            key=f"q_{i}",
                            label_visibility="collapsed",
                        )
                        # Extract the letter (first character)
                        user_answers[i] = choice[0] if choice else ""
                        st.markdown("")

                    submitted = st.form_submit_button("✅ Submit Quiz", type="primary")

                    if submitted:
                        from src.quiz.evaluator import evaluate_quiz

                        quiz_result = evaluate_quiz(
                            questions=questions,
                            answers=user_answers,
                            employee_id="preview",
                        )
                        st.session_state["quiz_result"] = quiz_result
                        st.session_state["quiz_submitted"] = True
                        st.rerun()

            # ── Show results ─────────────────────────────────────────
            if st.session_state.get("quiz_submitted") and "quiz_result" in st.session_state:
                quiz_result = st.session_state["quiz_result"]
                questions = st.session_state["quiz_questions"]

                st.markdown("---")
                st.markdown("### 📊 Quiz Results")

                # Score summary
                col_s, col_p, col_g = st.columns(3)
                with col_s:
                    st.markdown(
                        f'<div class="metric-card"><h3>Score</h3>'
                        f'<div class="value">{quiz_result.score} / {quiz_result.total}</div></div>',
                        unsafe_allow_html=True,
                    )
                with col_p:
                    st.markdown(
                        f'<div class="metric-card"><h3>Percentage</h3>'
                        f'<div class="value">{quiz_result.pct}%</div></div>',
                        unsafe_allow_html=True,
                    )
                with col_g:
                    grade = "🌟 Excellent" if quiz_result.pct >= 80 else "✅ Good" if quiz_result.pct >= 60 else "⚠️ Needs Improvement"
                    st.markdown(
                        f'<div class="metric-card"><h3>Grade</h3>'
                        f'<div class="value" style="font-size:1.2rem;">{grade}</div></div>',
                        unsafe_allow_html=True,
                    )

                # Per-question breakdown
                st.markdown("### 📋 Question Breakdown")
                for detail in quiz_result.details:
                    idx = detail["index"]
                    icon = "✅" if detail["is_correct"] else "❌"
                    q = questions[idx]

                    with st.expander(
                        f"{icon} Q{idx+1}: {q.question[:80]}{'…' if len(q.question) > 80 else ''}"
                    ):
                        st.markdown(f"**Skill:** {detail['skill_tag']}")
                        st.markdown(f"**Your answer:** {detail['submitted_answer']}")
                        st.markdown(f"**Correct answer:** {detail['correct_answer']}")
                        if not detail["is_correct"]:
                            # Show the correct option text
                            correct_letter = detail["correct_answer"]
                            correct_text = next(
                                (opt for opt in q.options if opt.startswith(correct_letter)),
                                correct_letter,
                            )
                            st.success(f"💡 {correct_text}")

                # Retake button
                if st.button("🔄 Generate New Quiz"):
                    for key in ["quiz_questions", "quiz_result", "quiz_submitted"]:
                        st.session_state.pop(key, None)
                    st.rerun()
