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
    initial_sidebar_state="expanded"
)

# Backend REST Endpoint Configuration
BACKEND_BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# --- Custom Styling & Design Matrix ---
st.markdown("""
    <style>
    .main {
        background-color: #0F172A;
    }
    .metric-container {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 12px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 600;
        background-color: #0284C7;
        color: white;
        margin-bottom: 8px;
    }
    .card-title {
        color: #F8FAFC;
        font-size: 1.15rem;
        font-weight: 600;
        margin-bottom: 6px;
    }
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

# --- Sidebar Health & Meta Information ---
with st.sidebar:
    st.markdown("### ⚙️ System Architecture")
    st.caption("Decoupled FastAPI Service + Streamlit Client")
    
    # Check Backend API Health
    try:
        health_resp = requests.get(f"{BACKEND_BASE_URL}/api/health", timeout=3)
        if health_resp.status_code == 200:
            st.success("🟢 REST API Backend: Online")
        else:
            st.warning(f"🟡 Backend Status: {health_resp.status_code}")
    except Exception:
        st.error("🔴 REST API Backend: Offline (Check port 8000)")

    st.markdown("---")
    st.markdown("**Core Pipelines:**")
    st.markdown("- 🔒 Regex PII Sanitization")
    st.markdown("- 🧠 Gemini Flash / Llama 3.3 Failover")
    st.markdown("- ⚡ Groq Whisper Audio STT")
    st.markdown("- 📊 Structured Pydantic Reports")

# --- Application Header ---
st.title("🎯 Mock AI Software Engineering Interviewer")
st.caption("Calibrated for Junior / Fresher Roles with PII Scrubbing and REST Microservice Architecture.")
st.markdown("---")

# ==============================================================================
# PHASE 1: CONFIGURATION & RESUME INGESTION
# ==============================================================================
if st.session_state.step == "UPLOAD":
    st.subheader("📋 Step 1: Ingest Resume & Calibrate Session")

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

    if uploaded_file is not None:
        if st.button("🚀 Initialize Mock Interview", type="primary", use_container_width=True):
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

    # Stepper Progress Bar
    progress = turn_idx / total_turns
    st.progress(progress, text=f"Question {turn_idx + 1} of {total_turns} — {st.session_state.round_type} Track")

    st.markdown(f'<span class="status-badge">{current_q.get("targeted_evaluation_node", "Concept Evaluation")}</span>', unsafe_allow_html=True)
    st.markdown(f"### ❓ Question {turn_idx + 1}: {current_q.get('question_text', '')}")

    st.markdown("---")
    st.subheader("🎙️ Candidate Response")

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
    st.subheader("📊 Candidate Performance Audit & ATS Diagnostic")

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
        col_score, col_critique = st.columns([1, 2])
        mb = report.get("metric_breakdown", {})

        with col_score:
            st.metric(label="Overall Candidate Score", value=f"{report.get('composite_score_out_of_10', 0)} / 10")
            st.markdown("#### Metric Breakdown")
            st.write(f"• **Technical Accuracy / Setup:** {mb.get('technical_accuracy_or_situation', 0)}/10")
            st.write(f"• **Communication Clarity:** {mb.get('communication_clarity', 0)}/10")
            st.write(f"• **Foundational Depth / Action:** {mb.get('foundational_depth_or_action', 0)}/10")

        with col_critique:
            st.markdown("#### Performance Critique")
            st.info(report.get("overall_performance_critique", ""))

        # ATS Alignment Section
        ats = report.get("ats_alignment")
        if ats:
            st.markdown("---")
            st.subheader("🎯 ATS Role Alignment Assessment")
            c1, c2 = st.columns([1, 2])
            with c1:
                st.metric(label="ATS Match Estimation", value=f"{ats.get('ats_match_percentage', 0)}%")
            with c2:
                matched = ats.get("matched_skills", [])
                missing = ats.get("missing_critical_skills", [])
                st.write("**Matched Skills:**", ", ".join(matched) if matched else "None explicitly detected")
                st.write("**Missing Keywords:**", ", ".join(missing) if missing else "None")
                
            tips = ats.get("resume_optimization_tips", [])
            if tips:
                st.markdown("**Resume Recommendations:**")
                for tip in tips:
                    st.markdown(f"- {tip}")

        # Actionable Improvements
        st.markdown("---")
        st.markdown("### 💡 Actionable Improvement Steps")
        for idx, feedback in enumerate(report.get("reconstructive_feedback", []), 1):
            st.markdown(f"**{idx}.** {feedback}")

        # Privacy Audit Metrics
        if st.session_state.redaction_metrics:
            with st.expander("🔒 Data Privacy & PII Redaction Audit"):
                st.json(st.session_state.redaction_metrics)

        # Download Reports Section
        st.markdown("---")
        st.subheader("📥 Export & Download Diagnostic Report")

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

        st.markdown("---")
        if st.button("🔄 Start New Interview Session", type="secondary"):
            st.session_state.step = "UPLOAD"
            st.session_state.resume_text = ""
            st.session_state.question_payload = []
            st.session_state.current_turn = 0
            st.session_state.transcript = []
            st.session_state.diagnostic_report = None
            st.session_state.redaction_metrics = {}
            st.rerun()