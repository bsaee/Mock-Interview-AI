import os
import requests
import streamlit as st
from pipeline.reporter import ReportGenerator
from parser.document import ResumeParsingEngine

# --- Application Configuration ---
st.set_page_config(
    page_title="AI Mock Interview Suite",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Backend REST Endpoint Configuration
BACKEND_BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# ==============================================================================
# DESIGN SYSTEM — Light, modern, sleek theme (no sidebar)
# ==============================================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Lexend:wght@500;600;700;800&display=swap');

    :root {
        --bg: #F6F7FB;
        --surface: #FFFFFF;
        --surface-alt: #F1F3F9;
        --border: #E7E9F1;
        --text-primary: #12141C;
        --text-secondary: #5B6172;
        --text-muted: #8A90A2;
        --accent: #5B5FEF;
        --accent-hover: #4A4EDB;
        --accent-soft: #EEEEFD;
        --accent-2: #8B5CF6;
        --success: #17A673;
        --success-soft: #E6F8F1;
        --warning: #B7791F;
        --warning-soft: #FEF3E0;
        --danger: #E1493F;
        --danger-soft: #FCEAE9;
        --radius-lg: 20px;
        --radius-md: 12px;
        --radius-sm: 8px;
        --shadow-sm: 0 1px 2px rgba(18,20,28,0.04), 0 1px 1px rgba(18,20,28,0.03);
        --shadow-md: 0 10px 28px rgba(18,20,28,0.07), 0 2px 6px rgba(18,20,28,0.04);
    }

    html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; }
    .stApp { background: var(--bg); }

    /* Hide sidebar entirely */
    section[data-testid="stSidebar"] { display: none !important; }
    div[data-testid="collapsedControl"] { display: none !important; }
    header[data-testid="stHeader"] { background: transparent; height: 0; }

    .block-container {
        padding-top: 1.6rem;
        padding-bottom: 4rem;
        max-width: 980px;
        margin: 0 auto;
    }

    hr { border: none; border-top: 1px solid var(--border); margin: 1.6rem 0; }
    p, li, label, span { color: var(--text-primary); }
    .stCaption, [data-testid="stCaptionContainer"] { color: var(--text-secondary) !important; }

    h1, h2, h3 { font-family: 'Lexend', sans-serif !important; color: var(--text-primary) !important; font-weight: 600 !important; }
    h3 { font-size: 1.1rem !important; }

    /* ---------- Top bar ---------- */
    .brand { display: flex; align-items: center; gap: 14px; }
    .brand-icon {
        width: 46px; height: 46px; border-radius: 14px;
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        display: flex; align-items: center; justify-content: center;
        font-size: 1.35rem; box-shadow: 0 6px 16px rgba(99,102,241,0.28); flex-shrink: 0;
    }
    .brand-title { font-family: 'Lexend', sans-serif; font-weight: 700; font-size: 1.32rem; color: var(--text-primary); line-height: 1.15; margin: 0; }
    .brand-subtitle { color: var(--text-secondary); font-size: 0.86rem; margin: 2px 0 0 0; }
    .status-chip {
        display: flex; align-items: center; gap: 7px; padding: 7px 13px; border-radius: 9999px;
        font-size: 0.8rem; font-weight: 600; white-space: nowrap; border: 1px solid transparent;
    }
    .status-chip.online { background: var(--success-soft); color: var(--success); border-color: rgba(23,166,115,0.22); }
    .status-chip.offline { background: var(--danger-soft); color: var(--danger); border-color: rgba(225,73,63,0.22); }
    .status-chip.warn { background: var(--warning-soft); color: var(--warning); border-color: rgba(183,121,31,0.22); }
    .status-dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }

    /* ---------- Stepper ---------- */
    .stepper { display: flex; align-items: center; gap: 0; margin: 18px 0 8px 0; }
    .step-item { display: flex; align-items: center; gap: 10px; flex: 0 0 auto; }
    .step-circle {
        width: 30px; height: 30px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.82rem; font-weight: 700;
        background: var(--surface-alt); color: var(--text-muted);
        border: 1.5px solid var(--border); flex-shrink: 0;
    }
    .step-circle.done { background: var(--success); color: white; border-color: var(--success); }
    .step-circle.active { background: var(--accent); color: white; border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-soft); }
    .step-label { font-size: 0.86rem; font-weight: 600; color: var(--text-muted); }
    .step-label.active { color: var(--text-primary); }
    .step-label.done { color: var(--text-secondary); }
    .step-line { flex: 1 1 auto; height: 2px; background: var(--border); margin: 0 14px; min-width: 30px; }
    .step-line.done { background: var(--success); }

    /* ---------- Real bordered containers (st.container(border=True)) ---------- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        box-shadow: var(--shadow-sm) !important;
        padding: 6px 8px !important;
        margin-bottom: 22px !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {
        gap: 0.6rem;
    }

    .card-header { display: flex; align-items: center; gap: 11px; margin: 6px 0 2px 6px; }
    .card-header .icon-badge {
        display: inline-flex; align-items: center; justify-content: center;
        width: 36px; height: 36px; border-radius: 11px;
        background: var(--accent-soft); font-size: 1.1rem; flex-shrink: 0;
    }
    .card-header .title-text { font-family: 'Lexend', sans-serif; font-weight: 600; font-size: 1.18rem; color: var(--text-primary); }
    .card-subtitle { color: var(--text-secondary); font-size: 0.89rem; margin: 2px 0 16px 53px; }

    .eval-badge {
        display: inline-block; padding: 5px 14px; border-radius: 9999px;
        font-size: 0.78rem; font-weight: 600;
        background: var(--accent-soft); color: var(--accent);
        margin: 6px 0 12px 6px; letter-spacing: 0.01em;
    }

    /* ---------- Buttons ---------- */
    .stButton > button {
        border-radius: var(--radius-md) !important;
        font-weight: 600 !important; font-size: 0.92rem !important;
        padding: 0.62rem 1.2rem !important;
        transition: all 0.15s ease !important;
        border: 1px solid var(--border) !important;
        background: var(--surface) !important;
        color: var(--text-primary) !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--accent) !important; border-color: var(--accent) !important; color: #fff !important;
        box-shadow: 0 4px 12px rgba(91,95,239,0.28) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--accent-hover) !important; border-color: var(--accent-hover) !important;
        box-shadow: 0 6px 16px rgba(91,95,239,0.36) !important; transform: translateY(-1px);
    }
    .stButton > button[kind="secondary"]:hover { background: var(--surface-alt) !important; border-color: var(--text-muted) !important; }
    .stDownloadButton > button {
        border-radius: var(--radius-md) !important; font-weight: 600 !important;
        background: var(--surface) !important; border: 1px solid var(--border) !important; color: var(--text-primary) !important;
    }
    .stDownloadButton > button:hover { background: var(--surface-alt) !important; border-color: var(--accent) !important; color: var(--accent) !important; }

    /* ---------- Inputs ---------- */
    .stTextInput input, .stTextArea textarea {
        background: var(--surface) !important; border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important; color: var(--text-primary) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent) !important; box-shadow: 0 0 0 3px var(--accent-soft) !important;
    }

    /* ---------- File uploader — force light styling regardless of theme ---------- */
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploaderDropzone"],
    [data-testid="stFileUploader"] > section > div {
        background: var(--surface-alt) !important;
        border: 1.5px dashed var(--border) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-secondary) !important;
    }
    [data-testid="stFileUploader"] section:hover,
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: var(--accent) !important;
    }
    [data-testid="stFileUploader"] section span,
    [data-testid="stFileUploader"] section small,
    [data-testid="stFileUploader"] section div {
        color: var(--text-secondary) !important;
    }
    [data-testid="stFileUploader"] button,
    [data-testid="stFileUploaderDropzone"] button {
        background: var(--surface) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
    }
    [data-testid="stFileUploader"] button:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
    }
    [data-testid="stFileUploaderFile"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
    }

    .stRadio [role="radiogroup"] label, .stCheckbox label { color: var(--text-primary) !important; font-size: 0.92rem; }
    .stSlider [data-baseweb="slider"] div[role="slider"] { background-color: var(--accent) !important; border-color: var(--accent) !important; }
    .stSlider [data-baseweb="slider"] > div > div { background: var(--accent) !important; }

    /* ---------- Progress ---------- */
    .stProgress > div > div > div > div { background: linear-gradient(90deg, #6366F1, #8B5CF6) !important; }
    .stProgress > div > div { background-color: var(--surface-alt) !important; border-radius: 9999px !important; }

    /* ---------- Tabs ---------- */
    .stTabs [data-baseweb="tab-list"] { gap: 6px; background: var(--surface-alt); padding: 5px; border-radius: var(--radius-md); }
    .stTabs [data-baseweb="tab"] { border-radius: var(--radius-sm); color: var(--text-secondary); font-weight: 600; font-size: 0.88rem; }
    .stTabs [aria-selected="true"] { background: var(--surface) !important; color: var(--accent) !important; box-shadow: var(--shadow-sm); }

    .stAlert { border-radius: var(--radius-md) !important; border: 1px solid var(--border) !important; }
    .streamlit-expanderHeader { background: var(--surface-alt) !important; border-radius: var(--radius-sm) !important; color: var(--text-primary) !important; font-weight: 600 !important; }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-thumb { background: #D3D7E2; border-radius: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }

    /* ---------- Score ring ---------- */
    .score-wrap { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 12px 0 4px 0; }
    .score-ring {
        width: 132px; height: 132px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        background: conic-gradient(var(--accent) calc(var(--pct) * 1%), var(--surface-alt) 0);
        position: relative;
    }
    .score-ring::before { content: ""; position: absolute; width: 106px; height: 106px; border-radius: 50%; background: var(--surface); }
    .score-ring .score-value { position: relative; z-index: 1; font-family: 'Lexend', sans-serif; font-weight: 700; font-size: 1.7rem; color: var(--text-primary); }
    .score-caption { margin-top: 12px; font-size: 0.86rem; font-weight: 600; color: var(--text-secondary); text-align: center; }

    /* ---------- Metric grid ---------- */
    .metric-grid { display: flex; flex-direction: column; gap: 12px; margin-top: 6px; }
    .metric-row { display: flex; align-items: center; gap: 12px; }
    .metric-row .metric-name { flex: 0 0 190px; font-size: 0.86rem; font-weight: 600; color: var(--text-secondary); }
    .metric-row .metric-bar-track { flex: 1 1 auto; height: 8px; border-radius: 9999px; background: var(--surface-alt); overflow: hidden; }
    .metric-row .metric-bar-fill { height: 100%; border-radius: 9999px; background: linear-gradient(90deg, #6366F1, #8B5CF6); }
    .metric-row .metric-value { flex: 0 0 44px; text-align: right; font-weight: 700; font-size: 0.86rem; color: var(--text-primary); }

    /* ---------- Skill chips ---------- */
    .chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 14px 0; }
    .chip { padding: 5px 12px; border-radius: 9999px; font-size: 0.82rem; font-weight: 600; }
    .chip.matched { background: var(--success-soft); color: var(--success); }
    .chip.missing { background: var(--danger-soft); color: var(--danger); }

    .feedback-item { display: flex; gap: 12px; padding: 12px 6px; border-bottom: 1px solid var(--border); }
    .feedback-item:last-child { border-bottom: none; }
    .feedback-num {
        flex-shrink: 0; width: 24px; height: 24px; border-radius: 50%;
        background: var(--accent-soft); color: var(--accent);
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.78rem;
    }
    .feedback-text { font-size: 0.92rem; color: var(--text-primary); line-height: 1.5; }
    </style>
""", unsafe_allow_html=True)

# --- Session State Management ---
if "step" not in st.session_state:
    st.session_state.step = "UPLOAD"  # UPLOAD -> INTERVIEW -> DIAGNOSTICS
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "redaction_metrics" not in st.session_state:
    st.session_state.redaction_metrics = {}
if "round_type" not in st.session_state:
    st.session_state.round_type = "Technical"
if "target_role" not in st.session_state:
    st.session_state.target_role = ""
if "job_description" not in st.session_state:
    st.session_state.job_description = ""
if "num_questions" not in st.session_state:
    st.session_state.num_questions = 4
if "question_payload" not in st.session_state:
    st.session_state.question_payload = []
if "current_turn" not in st.session_state:
    st.session_state.current_turn = 0
if "transcript" not in st.session_state:
    st.session_state.transcript = []
if "diagnostic_report" not in st.session_state:
    st.session_state.diagnostic_report = None

# --- Backend health check (used in top bar) ---
def get_status_chip_html():
    try:
        health_resp = requests.get(f"{BACKEND_BASE_URL}/api/health", timeout=3)
        if health_resp.status_code == 200:
            return '<div class="status-chip online"><span class="status-dot"></span>Backend Online</div>'
        return f'<div class="status-chip warn"><span class="status-dot"></span>Status {health_resp.status_code}</div>'
    except Exception:
        return '<div class="status-chip offline"><span class="status-dot"></span>Backend Offline</div>'

# --- Top bar (replaces sidebar) ---
top_l, top_r = st.columns([3, 1])
with top_l:
    st.markdown("""
        <div class="brand">
            <div class="brand-icon">🎯</div>
            <div>
                <p class="brand-title">Mock AI Software Engineering Interviewer</p>
                <p class="brand-subtitle">PII-safe resume parsing · Adaptive questions · ATS diagnostics</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
with top_r:
    st.markdown(f"<div style='display:flex; justify-content:flex-end; padding-top:10px;'>{get_status_chip_html()}</div>", unsafe_allow_html=True)

# --- Stepper ---
steps = [("UPLOAD", "1", "Setup"), ("INTERVIEW", "2", "Interview"), ("DIAGNOSTICS", "3", "Report")]
order = {"UPLOAD": 0, "INTERVIEW": 1, "DIAGNOSTICS": 2}
current_idx = order[st.session_state.step]

stepper_html = '<div class="stepper">'
for i, (key, num, label) in enumerate(steps):
    if i < current_idx:
        circle_cls, label_cls, content = "done", "done", "✓"
    elif i == current_idx:
        circle_cls, label_cls, content = "active", "active", num
    else:
        circle_cls, label_cls, content = "", "", num
    stepper_html += f'<div class="step-item"><div class="step-circle {circle_cls}">{content}</div><div class="step-label {label_cls}">{label}</div></div>'
    if i < len(steps) - 1:
        line_cls = "done" if i < current_idx else ""
        stepper_html += f'<div class="step-line {line_cls}"></div>'
stepper_html += '</div>'
st.markdown(stepper_html, unsafe_allow_html=True)

# ==============================================================================
# PHASE 1: CONFIGURATION & RESUME INGESTION
# ==============================================================================
if st.session_state.step == "UPLOAD":
    with st.container(border=True):
        st.markdown("""
            <div class="card-header">
                <span class="icon-badge">📋</span>
                <span class="title-text">Ingest Resume &amp; Calibrate Session</span>
            </div>
            <p class="card-subtitle">Upload a resume to begin. Add a target role below for optional ATS matching.</p>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1.4, 1])

        with col1:
            uploaded_file = st.file_uploader(
                "Upload Candidate Resume (.pdf or .docx)",
                type=["pdf", "docx"],
                help="Files are parsed and stripped of sensitive contact information before reaching the AI model."
            )

            enable_ats = st.checkbox("🎯 Target Specific Role / Job Description (Optional ATS Match)", value=False)
            target_role_val = ""
            jd_val = ""

            if enable_ats:
                target_role_val = st.text_input(
                    "Target Role Title:",
                    placeholder="e.g., Junior Python Developer, Associate Frontend Engineer"
                )

                jd_input_mode = st.radio(
                    "How would you like to provide the Job Description?",
                    options=["Upload JD Document (.pdf or .docx)", "Paste JD as Text"],
                    horizontal=True
                )

                if jd_input_mode == "Upload JD Document (.pdf or .docx)":
                    uploaded_jd_file = st.file_uploader(
                        "Upload Job Description (.pdf or .docx)",
                        type=["pdf", "docx"],
                        key="jd_file_uploader"
                    )
                    if uploaded_jd_file is not None:
                        try:
                            jd_bytes = uploaded_jd_file.read()
                            extracted_jd_text, _ = ResumeParsingEngine.process_file_stream(
                                uploaded_jd_file.name, jd_bytes, sanitize=False
                            )
                            jd_val = extracted_jd_text
                            st.success(f"✅ Loaded JD from `{uploaded_jd_file.name}`")
                        except Exception as err:
                            st.error(f"Failed to parse JD file: {str(err)}")
                else:
                    jd_val = st.text_area(
                        "Job Description Requirements:",
                        placeholder="Paste key responsibilities or tech stack requirements...",
                        height=120
                    )

        with col2:
            selected_round = st.radio(
                "Evaluation Track:",
                options=["Technical Fundamentals", "Behavioral STAR Round"],
                help="Technical: Project debugging, language mechanics, DBMS/OS fundamentals.\nBehavioral: STAR-based collaboration and ownership."
            )
            st.session_state.round_type = "Technical" if "Technical" in selected_round else "Behavioral"

            selected_num_questions = st.slider(
                "Session Length (Questions):",
                min_value=3,
                max_value=10,
                value=4,
                help="Number of questions generated for this interview round."
            )
            st.session_state.num_questions = selected_num_questions

        st.write("")
        init_clicked = st.button("🚀 Initialize Mock Interview", type="primary", use_container_width=True)

    if init_clicked:
        if uploaded_file is None:
            st.warning("⚠️ Please upload a candidate resume before starting the interview.")
        else:
            with st.spinner("Processing resume through FastAPI PII redaction and generation endpoints..."):
                try:
                    # 1. Call REST endpoint to parse and sanitize resume
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    parse_resp = requests.post(f"{BACKEND_BASE_URL}/api/resume/parse-and-sanitize", files=files)

                    if parse_resp.status_code != 200:
                        st.error(f"Resume Parsing Failed: {parse_resp.text}")
                        st.stop()

                    parse_data = parse_resp.json()
                    st.session_state.resume_text = parse_data["sanitized_resume_text"]
                    st.session_state.redaction_metrics = parse_data["redaction_audit"]
                    st.session_state.target_role = target_role_val.strip()
                    st.session_state.job_description = jd_val.strip()

                    # 2. Call REST endpoint to generate question payload
                    gen_payload = {
                        "resume_text": st.session_state.resume_text,
                        "round_type": st.session_state.round_type,
                        "target_role": st.session_state.target_role or "Entry-Level / Junior Software Engineer",
                        "job_description": st.session_state.job_description or "General Software Development Fundamentals",
                        "num_questions": st.session_state.num_questions
                    }
                    gen_resp = requests.post(f"{BACKEND_BASE_URL}/api/interview/generate-questions", json=gen_payload)

                    if gen_resp.status_code != 200:
                        st.error(f"Question Generation Failed: {gen_resp.text}")
                        st.stop()

                    questions_data = gen_resp.json()
                    st.session_state.question_payload = questions_data.get("questions", [])
                    st.session_state.current_turn = 0
                    st.session_state.transcript = []
                    st.session_state.step = "INTERVIEW"
                    st.rerun()

                except Exception as ex:
                    st.error(f"❌ Communication Error with FastAPI Backend: {str(ex)}")

# ==============================================================================
# PHASE 2: MULTI-TURN INTERVIEW EXECUTION LOOP
# ==============================================================================
elif st.session_state.step == "INTERVIEW":
    turn_idx = st.session_state.current_turn
    total_turns = len(st.session_state.question_payload)

    if turn_idx >= total_turns:
        st.session_state.step = "DIAGNOSTICS"
        st.rerun()

    current_q = st.session_state.question_payload[turn_idx]

    st.progress(turn_idx / total_turns, text=f"Question {turn_idx + 1} of {total_turns} — {st.session_state.round_type} Track")

    with st.container(border=True):
        st.markdown(f'<span class="eval-badge">{current_q.get("targeted_evaluation_node", "Concept Evaluation")}</span>', unsafe_allow_html=True)
        st.markdown(f"### ❓ Question {turn_idx + 1}")
        st.write(current_q.get('question_text', ''))

    with st.container(border=True):
        st.markdown("""
            <div class="card-header">
                <span class="icon-badge">🎙️</span>
                <span class="title-text">Candidate Response</span>
            </div>
        """, unsafe_allow_html=True)

        tab_voice, tab_text = st.tabs(["🎤 Voice Recording (Microphone)", "⌨️ Text Response"])
        candidate_answer = ""

        with tab_voice:
            audio_record = st.audio_input("Record your answer:")
            if audio_record is not None:
                with st.spinner("Streaming binary audio buffer to FastAPI Groq Whisper service..."):
                    try:
                        audio_files = {"file": ("input.wav", audio_record.getvalue(), "audio/wav")}
                        stt_resp = requests.post(f"{BACKEND_BASE_URL}/api/audio/transcribe", files=audio_files)
                        if stt_resp.status_code == 200:
                            candidate_answer = stt_resp.json().get("transcription", "")
                            st.success("Transcribed Successfully!")
                            st.write(f"**Transcription:** {candidate_answer}")
                        else:
                            st.error(f"STT Error: {stt_resp.text}")
                    except Exception as err:
                        st.error(f"Failed to reach STT endpoint: {str(err)}")

        with tab_text:
            typed_answer = st.text_area("Type your response:", height=130, key=f"text_area_{turn_idx}")
            if typed_answer.strip():
                candidate_answer = typed_answer.strip()

        st.write("")
        if st.button("Submit Answer & Advance ➡️", type="primary"):
            if not candidate_answer.strip():
                st.warning("⚠️ Please provide a voice or text answer before submitting.")
            else:
                st.session_state.transcript.append({
                    "question_id": current_q.get("question_id", turn_idx + 1),
                    "targeted_node": current_q.get("targeted_evaluation_node", ""),
                    "question": current_q.get("question_text", ""),
                    "answer": candidate_answer
                })
                st.session_state.current_turn += 1
                st.rerun()

# ==============================================================================
# PHASE 3: DIAGNOSTIC REPORT & EXPORT MATRIX
# ==============================================================================
elif st.session_state.step == "DIAGNOSTICS":
    if st.session_state.diagnostic_report is None:
        with st.spinner("Aggregating transcript and invoking FastAPI evaluation engine..."):
            try:
                eval_payload = {
                    "transcript": st.session_state.transcript,
                    "target_role": st.session_state.target_role or "",
                    "job_description": st.session_state.job_description or "",
                    "resume_text": st.session_state.resume_text
                }
                eval_resp = requests.post(f"{BACKEND_BASE_URL}/api/interview/evaluate", json=eval_payload)
                if eval_resp.status_code != 200:
                    st.error(f"Evaluation Failed: {eval_resp.text}")
                    st.stop()
                st.session_state.diagnostic_report = eval_resp.json()
            except Exception as ex:
                st.error(f"Backend Communication Error: {str(ex)}")
                st.stop()

    report = st.session_state.diagnostic_report

    if report:
        mb = report.get("metric_breakdown", {})
        score = report.get('composite_score_out_of_10', 0)
        pct = max(0, min(100, float(score) * 10))

        with st.container(border=True):
            st.markdown("""
                <div class="card-header">
                    <span class="icon-badge">📊</span>
                    <span class="title-text">Candidate Performance Audit</span>
                </div>
            """, unsafe_allow_html=True)

            col_score, col_critique = st.columns([1, 2])
            with col_score:
                st.markdown(f"""
                    <div class="score-wrap">
                        <div class="score-ring" style="--pct:{pct};">
                            <div class="score-value">{score}/10</div>
                        </div>
                        <div class="score-caption">Overall Candidate Score</div>
                    </div>
                """, unsafe_allow_html=True)

            with col_critique:
                st.markdown("#### Metric Breakdown")
                metrics = [
                    ("Technical Accuracy / Setup", mb.get('technical_accuracy_or_situation', 0)),
                    ("Communication Clarity", mb.get('communication_clarity', 0)),
                    ("Foundational Depth / Action", mb.get('foundational_depth_or_action', 0)),
                ]
                rows_html = '<div class="metric-grid">'
                for name, val in metrics:
                    width = max(0, min(100, float(val) * 10))
                    rows_html += f"""
                        <div class="metric-row">
                            <div class="metric-name">{name}</div>
                            <div class="metric-bar-track"><div class="metric-bar-fill" style="width:{width}%;"></div></div>
                            <div class="metric-value">{val}/10</div>
                        </div>
                    """
                rows_html += '</div>'
                st.markdown(rows_html, unsafe_allow_html=True)

            st.markdown("#### Performance Critique")
            st.info(report.get("overall_performance_critique", ""))

        # ATS Alignment Section
        ats = report.get("ats_alignment")
        if ats:
            with st.container(border=True):
                st.markdown("""
                    <div class="card-header">
                        <span class="icon-badge">🎯</span>
                        <span class="title-text">ATS Role Alignment Assessment</span>
                    </div>
                """, unsafe_allow_html=True)
                c1, c2 = st.columns([1, 2])
                with c1:
                    ats_pct = ats.get('ats_match_percentage', 0)
                    st.markdown(f"""
                        <div class="score-wrap">
                            <div class="score-ring" style="--pct:{ats_pct};">
                                <div class="score-value">{ats_pct}%</div>
                            </div>
                            <div class="score-caption">ATS Match Estimation</div>
                        </div>
                    """, unsafe_allow_html=True)
                with c2:
                    matched = ats.get("matched_skills", [])
                    missing = ats.get("missing_critical_skills", [])

                    st.markdown("**Matched Skills**")
                    if matched:
                        chips = "".join(f'<span class="chip matched">{s}</span>' for s in matched)
                        st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)
                    else:
                        st.caption("None explicitly detected")

                    st.markdown("**Missing Keywords**")
                    if missing:
                        chips = "".join(f'<span class="chip missing">{s}</span>' for s in missing)
                        st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)
                    else:
                        st.caption("None")

                tips = ats.get("resume_optimization_tips", [])
                if tips:
                    st.markdown("**Resume Recommendations**")
                    for tip in tips:
                        st.markdown(f"- {tip}")

        # Actionable Improvements
        with st.container(border=True):
            st.markdown("""
                <div class="card-header">
                    <span class="icon-badge">💡</span>
                    <span class="title-text">Actionable Improvement Steps</span>
                </div>
            """, unsafe_allow_html=True)
            feedback_html = ""
            for idx, feedback in enumerate(report.get("reconstructive_feedback", []), 1):
                feedback_html += f"""
                    <div class="feedback-item">
                        <div class="feedback-num">{idx}</div>
                        <div class="feedback-text">{feedback}</div>
                    </div>
                """
            st.markdown(feedback_html, unsafe_allow_html=True)

            if st.session_state.redaction_metrics:
                with st.expander("🔒 Data Privacy & PII Redaction Audit"):
                    st.json(st.session_state.redaction_metrics)

        # Download Reports Section
        with st.container(border=True):
            st.markdown("""
                <div class="card-header">
                    <span class="icon-badge">📥</span>
                    <span class="title-text">Export &amp; Download Diagnostic Report</span>
                </div>
            """, unsafe_allow_html=True)

            class ReportAdapter:
                def __init__(self, data):
                    self.composite_score_out_of_10 = data.get("composite_score_out_of_10", 0)
                    self.overall_performance_critique = data.get("overall_performance_critique", "")
                    self.reconstructive_feedback = data.get("reconstructive_feedback", [])

                    class MB:
                        def __init__(self, d):
                            self.technical_accuracy_or_situation = d.get("technical_accuracy_or_situation", 0)
                            self.communication_clarity = d.get("communication_clarity", 0)
                            self.foundational_depth_or_action = d.get("foundational_depth_or_action", 0)
                    self.metric_breakdown = MB(data.get("metric_breakdown", {}))

                    ats_d = data.get("ats_alignment")
                    if ats_d:
                        class ATS:
                            def __init__(self, a):
                                self.ats_match_percentage = a.get("ats_match_percentage", 0)
                                self.matched_skills = a.get("matched_skills", [])
                                self.missing_critical_skills = a.get("missing_critical_skills", [])
                                self.resume_optimization_tips = a.get("resume_optimization_tips", [])
                        self.ats_alignment = ATS(ats_d)
                    else:
                        self.ats_alignment = None

            adapter_report = ReportAdapter(report)
            md_content = ReportGenerator.generate_markdown_report(
                adapter_report,
                st.session_state.transcript,
                st.session_state.round_type,
                st.session_state.target_role
            )
            pdf_bytes = ReportGenerator.generate_pdf_report(
                adapter_report,
                st.session_state.transcript,
                st.session_state.round_type,
                st.session_state.target_role
            )

            dl1, dl2 = st.columns(2)
            with dl1:
                st.download_button(
                    "📄 Download Markdown (.md)",
                    data=md_content,
                    file_name="interview_report.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            with dl2:
                st.download_button(
                    "📑 Download PDF Audit Card (.pdf)",
                    data=pdf_bytes,
                    file_name="interview_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

        if st.button("🔄 Start New Interview Session", type="secondary", use_container_width=True):
            st.session_state.step = "UPLOAD"
            st.session_state.resume_text = ""
            st.session_state.question_payload = []
            st.session_state.current_turn = 0
            st.session_state.transcript = []
            st.session_state.diagnostic_report = None
            st.session_state.redaction_metrics = {}
            st.rerun()