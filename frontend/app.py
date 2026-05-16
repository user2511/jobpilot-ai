# frontend/app.py
# Complete Streamlit UI for JobPilot.
# Single file — minimal but polished and fully functional.

import streamlit as st
import httpx
import os

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="JobPilot — AI Job Application Optimizer",
    page_icon="🚀",
    layout="centered"
)

# ─── Custom CSS for clean look ────────────────────────────────────────────────
st.markdown("""
<style>
    .main { padding-top: 2rem; }
    .stAlert { border-radius: 8px; }
    .metric-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #e0e0e0;
    }
    .score-high { color: #1D9E75; font-size: 2rem; font-weight: bold; }
    .score-mid  { color: #EF9F27; font-size: 2rem; font-weight: bold; }
    .score-low  { color: #E24B4A; font-size: 2rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ─── Session state init ───────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "resume_name" not in st.session_state:
    st.session_state.resume_name = None
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None


# ─── Helper functions ─────────────────────────────────────────────────────────

def api_post(endpoint: str, **kwargs) -> dict:
    """POST request to backend API."""
    try:
        r = httpx.post(f"{API_BASE}{endpoint}", timeout=120.0, **kwargs)
        r.raise_for_status()
        return r.json()
    except httpx.TimeoutException:
        st.error("⏱️ Request timed out. The AI model is processing — please try again.")
        return None
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", str(e))
        st.error(f"❌ Error: {detail}")
        return None
    except Exception as e:
        st.error(f"❌ Connection error: {e}. Is the backend running?")
        return None


def score_color_class(score: int) -> str:
    if score >= 70: return "score-high"
    if score >= 45: return "score-mid"
    return "score-low"


# ─── Header ───────────────────────────────────────────────────────────────────
st.title("🚀 JobPilot")
st.caption("AI-powered job application optimizer — tailor your resume, generate cover letters, craft outreach")
st.divider()


# ─── STEP 1: Upload Resume ────────────────────────────────────────────────────
st.subheader("Step 1 — Upload Your Resume")

if st.session_state.session_id:
    st.success(f"✅ Resume loaded: **{st.session_state.resume_name}**")
    if st.button("Upload a different resume", type="secondary"):
        st.session_state.session_id = None
        st.session_state.resume_name = None
        st.session_state.analysis_result = None
        st.rerun()
else:
    uploaded_file = st.file_uploader(
        "Upload your master resume (PDF)",
        type=["pdf"],
        help="Upload once — reuse for multiple job applications"
    )

    if uploaded_file:
        with st.spinner("📄 Parsing your resume with AI..."):
            response = api_post(
                "/resume/upload",
                files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            )
        if response:
            st.session_state.session_id = response["session_id"]
            st.session_state.resume_name = uploaded_file.name
            st.success(f"✅ Resume parsed! Found **{response['skills_count']} skills** and **{response['experience_count']} roles**.")
            st.rerun()

st.divider()


# ─── STEP 2: Job Description ──────────────────────────────────────────────────
st.subheader("Step 2 — Add Job Description")

if not st.session_state.session_id:
    st.info("⬆️ Upload your resume first to continue")
else:
    jd_input_method = st.radio(
        "How would you like to provide the job description?",
        ["Paste text", "Enter URL"],
        horizontal=True
    )

    jd_text = None
    jd_url = None

    if jd_input_method == "Paste text":
        jd_text = st.text_area(
            "Paste job description here",
            height=200,
            placeholder="Paste the full job description text here..."
        )
    else:
        jd_url = st.text_input(
            "Job posting URL",
            placeholder="https://jobs.company.com/role/..."
        )

    analyze_clicked = st.button(
        "🔍 Analyze & Generate",
        type="primary",
        disabled=not (jd_text or jd_url)
    )

    if analyze_clicked:
        payload = {"session_id": st.session_state.session_id}
        if jd_text:
            payload["jd_text"] = jd_text
        else:
            payload["jd_url"] = jd_url

        with st.spinner("🤖 AI is analyzing your fit, rewriting bullets, and generating materials... (this takes ~30–60s)"):
            result = api_post("/jobs/analyze", json=payload)

        if result:
            st.session_state.analysis_result = result
            st.success("✅ Analysis complete!")
            st.rerun()


# ─── STEP 3: Results ─────────────────────────────────────────────────────────
if st.session_state.analysis_result:
    st.divider()
    st.subheader("Step 3 — Your Results")

    output = st.session_state.analysis_result["output"]
    match  = output["match_result"]
    score  = match["fit_score"]

    # Role info
    st.markdown(f"### {output['role_title']} @ {output['company_name']}")

    # Fit score prominently
    col1, col2, col3 = st.columns(3)
    with col1:
        css_class = score_color_class(score)
        st.markdown(f"<div class='metric-card'><div class='{css_class}'>{score}</div><div>Fit Score</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><div style='font-size:1.5rem;font-weight:bold;color:#1D9E75'>{len(match['matched_skills'])}</div><div>Skills Matched</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><div style='font-size:1.5rem;font-weight:bold;color:#E24B4A'>{len(match['missing_skills'])}</div><div>Skills Missing</div></div>", unsafe_allow_html=True)

    st.divider()

    # Tabs for each output section
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Match Analysis", "✏️ Optimized Bullets", "📝 Cover Letter", "📬 Recruiter Outreach"])

    with tab1:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**✅ Matched Skills**")
            if match["matched_skills"]:
                for s in match["matched_skills"]:
                    st.markdown(f"- {s}")
            else:
                st.caption("None matched")

        with col_b:
            st.markdown("**❌ Missing Skills**")
            if match["missing_skills"]:
                for s in match["missing_skills"]:
                    st.markdown(f"- {s}")
            else:
                st.caption("None missing — great fit!")

        if match["improvement_suggestions"]:
            st.markdown("**💡 Improvement Suggestions**")
            for suggestion in match["improvement_suggestions"]:
                st.info(suggestion)

        if match["weak_sections"]:
            st.markdown("**⚠️ Weak Sections**")
            for section in match["weak_sections"]:
                st.warning(section)

    with tab2:
        bullets = output["optimized_bullets"]
        if bullets["rewritten_bullets"]:
            for i, (orig, rewritten) in enumerate(
                zip(bullets["original_bullets"], bullets["rewritten_bullets"]), 1
            ):
                with st.expander(f"Bullet {i}"):
                    col_o, col_r = st.columns(2)
                    with col_o:
                        st.markdown("**Original**")
                        st.markdown(orig)
                    with col_r:
                        st.markdown("**Rewritten**")
                        st.markdown(f"**{rewritten}**")
        else:
            st.info("No bullets found to optimize")

    with tab3:
        cover_letter_text = output["cover_letter"]["content"]
        st.markdown(f"**Word count:** {output['cover_letter']['word_count']}")
        st.text_area("Cover Letter", value=cover_letter_text, height=300, key="cl_display")
        st.download_button(
            "⬇️ Download Cover Letter",
            data=cover_letter_text,
            file_name=f"cover_letter_{output['role_title'].replace(' ', '_')}.txt",
            mime="text/plain"
        )

    with tab4:
        outreach = output["recruiter_outreach"]
        st.markdown(f"**Subject Line:** `{outreach['subject_line']}`")
        st.text_area("Message", value=outreach["message_body"], height=200, key="out_display")
        full_outreach = f"Subject: {outreach['subject_line']}\n\n{outreach['message_body']}"
        st.download_button(
            "⬇️ Download Outreach Message",
            data=full_outreach,
            file_name="recruiter_outreach.txt",
            mime="text/plain"
        )

    st.divider()
    if st.button("🔄 Analyze Another Job", type="secondary"):
        st.session_state.analysis_result = None
        st.rerun()
