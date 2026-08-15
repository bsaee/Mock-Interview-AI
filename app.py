import os
import tempfile
import streamlit as st
from dotenv import load_dotenv
from pipeline.reporter import ReportGenerator

# Load environment variables from .env file
load_dotenv()

from langchain_groq import ChatGroq
from core.config import EngineConfiguration
from parser.document import ResumeParsingEngine
from parser.audio import AudioOrchestrationEngine
from pipeline.templates import MockInterviewPrompts
from pipeline.evaluation import QuestionGenerationMatrix, DiagnosticReportSchema

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Mock Interview Suite",
    page_icon="🎯",
    layout="wide"
)

# Initialize Engine Clients
@st.cache_resource
def load_system_configs():
    config = EngineConfiguration()
    return config.get_llm_client(), config.get_transcription_client()

try:
    llm_client, transcription_client = load_system_configs()
except Exception as err:
    st.error(f"❌ Configuration Initialization Error: {str(err)}")
    st.stop()

# --- Session State Management ---
if "step" not in st.session_state:
    st.session_state.step = "UPLOAD"  # Valid steps: UPLOAD, INTERVIEW, DIAGNOSTICS
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

# --- Application Header ---
st.title("🎯 Mock AI Software Engineering Interviewer")
st.caption("Junior / Fresher Technical & Behavioral STAR Interview Assessment with Privacy Guardrails.")
st.markdown("---")

# ==============================================================================
# PHASE 1: RESUME UPLOAD & CONFIGURATION
# ==============================================================================
if st.session_state.step == "UPLOAD":
    st.subheader("📋 Step 1: Upload Resume & Configure Session")
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload Candidate Resume (.pdf or .docx)", 
            type=["pdf", "docx"],
            help="Your resume will be parsed and sensitive PII (email, phone, URLs) will be automatically redacted before processing."
        )
        
        # Optional Role / ATS Target Section
        enable_role_target = st.checkbox("🎯 Target Specific Role / Job Description (Optional ATS Match)", value=False)
        
        target_role_input = ""
        jd_input = ""
        if enable_role_target:
            target_role_input = st.text_input(
                "Target Role / Title:", 
                placeholder="e.g., Junior Python Backend Developer, Associate QA Engineer"
            )
            jd_input = st.text_area(
                "Paste Job Description (JD):", 
                placeholder="Paste key responsibilities or required technologies from the job posting...",
                height=120
            )

    with col2:
        selected_round = st.radio(
            "Select Evaluation Round:",
            options=["Technical Fundamentals", "Behavioral STAR Round"],
            help="Technical: Project architecture, basic debugging, language mechanics, DBMS/OS fundamentals.\nBehavioral: STAR-based collaboration, deadline handling, and ownership."
        )
        
        st.session_state.round_type = "Technical" if "Technical" in selected_round else "Behavioral"
        
        # Dynamic Question Count Slider (3 - 10)
        selected_num_questions = st.slider(
            "Number of Interview Questions:",
            min_value=3,
            max_value=10,
            value=4,
            help="Configure interview length (3 to 10 questions)."
        )
        st.session_state.num_questions = selected_num_questions

    if uploaded_file is not None:
        if st.button("🚀 Start Interview Session", type="primary", use_container_width=True):
            with st.spinner("Sanitizing PII and generating personalized interview questions..."):
                try:
                    # 1. Parse and sanitize resume
                    file_bytes = uploaded_file.read()
                    sanitized_text, audit_counts = ResumeParsingEngine.process_file_stream(
                        uploaded_file.name, file_bytes, sanitize=True
                    )
                    
                    st.session_state.resume_text = sanitized_text
                    st.session_state.redaction_metrics = audit_counts
                    st.session_state.target_role = target_role_input.strip()
                    st.session_state.job_description = jd_input.strip()
                    
                    # 2. Select prompt template
                    if st.session_state.round_type == "Technical":
                        prompt_template = MockInterviewPrompts.get_technical_generation_template()
                    else:
                        prompt_template = MockInterviewPrompts.get_behavioral_generation_template()
                        
                    # 3. Setup Primary LLM (Gemini) + Backup LLM (Groq Llama 3.3)
                    primary_llm = llm_client.with_structured_output(QuestionGenerationMatrix)
                    backup_llm = ChatGroq(
                        model="llama-3.3-70b-versatile",
                        groq_api_key=EngineConfiguration().groq_key,
                        temperature=0.3
                    ).with_structured_output(QuestionGenerationMatrix)
                    
                    structured_chain = prompt_template | primary_llm.with_fallbacks([backup_llm])
                    
                    response_matrix = structured_chain.invoke({
                        "resume_text": st.session_state.resume_text,
                        "target_role": st.session_state.target_role or "Entry-Level / Junior Software Engineer",
                        "job_description": st.session_state.job_description or "General Software Development Fundamentals",
                        "num_questions": st.session_state.num_questions
                    })
                    
                    # 4. Save state & advance to interview
                    st.session_state.question_payload = response_matrix.questions
                    st.session_state.current_turn = 0
                    st.session_state.transcript = []
                    st.session_state.step = "INTERVIEW"
                    st.rerun()
                    
                except Exception as ex:
                    st.error(f"❌ Failed to initialize interview: {str(ex)}")

# ==============================================================================
# PHASE 2: MULTI-TURN INTERVIEW LOOP
# ==============================================================================
elif st.session_state.step == "INTERVIEW":
    turn_idx = st.session_state.current_turn
    total_turns = len(st.session_state.question_payload)
    
    # Check completion
    if turn_idx >= total_turns:
        st.session_state.step = "DIAGNOSTICS"
        st.rerun()
        
    current_q = st.session_state.question_payload[turn_idx]
    
    # Progress & Header
    progress_val = (turn_idx) / total_turns
    st.progress(progress_val, text=f"Question {turn_idx + 1} of {total_turns} ({st.session_state.round_type} Round)")
    
    # Question Card
    st.info(f"**Focus Concept:** {current_q.targeted_evaluation_node}")
    st.markdown(f"### ❓ Question {turn_idx + 1}: {current_q.question_text}")
    
    # Audio Question Playback via edge-tts
    audio_filename = f"q_{turn_idx + 1}.mp3"
    audio_file_path = os.path.join("static", "cache", audio_filename)
    
    if not os.path.exists(audio_file_path):
        with st.spinner("Synthesizing question audio..."):
            try:
                AudioOrchestrationEngine.synthesize_speech(current_q.question_text, audio_filename)
            except Exception:
                pass  # Fallback gracefully to text if TTS hits service issues
            
    if os.path.exists(audio_file_path):
        st.audio(audio_file_path, format="audio/mp3")

    st.markdown("---")
    st.subheader("🎙️ Your Response")
    
    input_tab1, input_tab2 = st.tabs(["🎤 Microphone Voice Input", "⌨️ Text Input"])
    
    candidate_answer = ""
    
    with input_tab1:
        recorded_audio = st.audio_input("Record your spoken answer:")
        if recorded_audio is not None:
            with st.spinner("Transcribing your answer via Groq Whisper..."):
                try:
                    audio_bytes = recorded_audio.read()
                    candidate_answer = AudioOrchestrationEngine.transcribe_audio_stream(
                        audio_bytes, f"turn_{turn_idx + 1}.wav"
                    )
                    st.success("Audio transcribed successfully!")
                    st.write(f"**Transcribed Text:** {candidate_answer}")
                except Exception as err:
                    st.error(f"Transcription error: {str(err)}")
                    
    with input_tab2:
        text_answer = st.text_area(
            "Or type your answer here:", 
            height=130, 
            key=f"text_input_{turn_idx}"
        )
        if text_answer.strip():
            candidate_answer = text_answer.strip()

    st.write("")
    if st.button("Submit Answer & Next Question ➡️", type="primary"):
        if not candidate_answer.strip():
            st.warning("⚠️ Please provide an answer via microphone or text before proceeding.")
        else:
            st.session_state.transcript.append({
                "question_id": current_q.question_id,
                "targeted_node": current_q.targeted_evaluation_node,
                "question": current_q.question_text,
                "answer": candidate_answer
            })
            st.session_state.current_turn += 1
            st.rerun()

# ==============================================================================
# PHASE 3: COMPREHENSIVE DIAGNOSTIC ASSESSMENT & ATS SCORECARD
# ==============================================================================
elif st.session_state.step == "DIAGNOSTICS":
    st.subheader("📊 Post-Interview Diagnostic & Performance Report")
    
    has_ats_context = bool(st.session_state.target_role or st.session_state.job_description)
    
    if st.session_state.diagnostic_report is None:
        with st.spinner("Auditing interview transcript and compiling evaluation report..."):
            try:
                # Compile Transcript String
                transcript_str = ""
                for entry in st.session_state.transcript:
                    transcript_str += f"Question [{entry['targeted_node']}]: {entry['question']}\n"
                    transcript_str += f"Candidate Answer: {entry['answer']}\n\n"
                    
                eval_template = MockInterviewPrompts.get_evaluation_template(include_ats=has_ats_context)
                
                primary_evaluator = llm_client.with_structured_output(DiagnosticReportSchema)
                backup_evaluator = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    groq_api_key=EngineConfiguration().groq_key,
                    temperature=0.3
                ).with_structured_output(DiagnosticReportSchema)
                
                eval_chain = eval_template | primary_evaluator.with_fallbacks([backup_evaluator])
                
                st.session_state.diagnostic_report = eval_chain.invoke({
                    "interview_transcript": transcript_str,
                    "target_role": st.session_state.target_role or "N/A",
                    "job_description": st.session_state.job_description or "N/A",
                    "resume_text": st.session_state.resume_text
                })
            except Exception as ex:
                st.error(f"❌ Failed to generate evaluation report: {str(ex)}")
                st.stop()
                
    report = st.session_state.diagnostic_report
    
    if report:
        # Scorecard
        col_score, col_critique = st.columns([1, 2])
        
        with col_score:
            st.metric(label="Composite Score", value=f"{report.composite_score_out_of_10} / 10")
            st.markdown("#### Metric Breakdown")
            st.write(f"• **Technical Accuracy / Setup:** {report.metric_breakdown.technical_accuracy_or_situation}/10")
            st.write(f"• **Communication Clarity:** {report.metric_breakdown.communication_clarity}/10")
            st.write(f"• **Foundational Depth / STAR Action:** {report.metric_breakdown.foundational_depth_or_action}/10")
            
        with col_critique:
            st.markdown("#### Performance Critique")
            st.info(report.overall_performance_critique)
            
        # Optional ATS Alignment Card
        if report.ats_alignment:
            st.markdown("---")
            st.subheader("🎯 ATS Role Alignment Assessment")
            ats = report.ats_alignment
            
            ats_col1, ats_col2 = st.columns([1, 2])
            with ats_col1:
                st.metric(label="ATS Match Estimation", value=f"{ats.ats_match_percentage}%")
            with ats_col2:
                st.write("**Matched Skills:**", ", ".join(ats.matched_skills) if ats.matched_skills else "None explicitly detected")
                st.write("**Missing Critical Keywords:**", ", ".join(ats.missing_critical_skills) if ats.missing_critical_skills else "None")
                
            if ats.resume_optimization_tips:
                st.markdown("**ATS Optimization Recommendations:**")
                for tip in ats.resume_optimization_tips:
                    st.markdown(f"- {tip}")

        # Actionable Improvements
        st.markdown("---")
        st.markdown("### 💡 Actionable Improvement Steps")
        for idx, feedback in enumerate(report.reconstructive_feedback, 1):
            st.markdown(f"**{idx}.** {feedback}")

        # Privacy Redaction Audit
        if st.session_state.redaction_metrics:
            with st.expander("🔒 Data Privacy & PII Redaction Audit"):
                st.write("The following sensitive items were redacted prior to AI processing:")
                st.json(st.session_state.redaction_metrics)

        # --- Downloadable Reports Section ---
        st.markdown("---")
        st.subheader("📥 Export & Download Diagnostic Report")
        
        md_content = ReportGenerator.generate_markdown_report(
            report_data=report,
            transcript=st.session_state.transcript,
            round_type=st.session_state.round_type,
            target_role=st.session_state.target_role
        )
        
        pdf_bytes = ReportGenerator.generate_pdf_report(
            report_data=report,
            transcript=st.session_state.transcript,
            round_type=st.session_state.round_type,
            target_role=st.session_state.target_role
        )
        
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                label="📄 Download Report as Markdown (.md)",
                data=md_content,
                file_name="interview_diagnostic_report.md",
                mime="text/markdown",
                use_container_width=True
            )
        with dl_col2:
            st.download_button(
                label="📑 Download Full PDF Audit Card (.pdf)",
                data=pdf_bytes,
                file_name="interview_diagnostic_report.pdf",
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