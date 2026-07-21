import os
import streamlit as st
from dotenv import load_dotenv

# Force-load environment variables from .env file before initializing configs
load_dotenv()

from langchain_groq import ChatGroq
from core.config import EngineConfiguration
from parser.document import ResumeParsingEngine
from parser.audio import AudioOrchestrationEngine
from pipeline.templates import MockInterviewPrompts
from pipeline.evaluation import QuestionGenerationMatrix, DiagnosticReportSchema

# --- Page Setup & Configuration ---
st.set_page_config(
    page_title="AI Engineering Interview Suite",
    page_icon="🎯",
    layout="wide"
)

# Initialize global engine configurations
@st.cache_resource
def load_system_configs():
    config = EngineConfiguration()
    return config.get_llm_client(), config.get_transcription_client()

try:
    llm_client, transcription_client = load_system_configs()
except Exception as err:
    st.error(f"❌ Configuration Initialization Error: {str(err)}")
    st.stop()

# --- Session State Memory Matrix Initialization ---
if "step" not in st.session_state:
    st.session_state.step = "UPLOAD"  # Valid steps: UPLOAD, INTERVIEW, DIAGNOSTICS
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "round_type" not in st.session_state:
    st.session_state.round_type = "Technical"
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
st.caption("AI-powered technical project architecture, CS fundamentals, and STAR behavioral assessment system.")
st.markdown("---")

# ==============================================================================
# PHASE 1: RESUME UPLOAD & ROUND CONFIGURATION
# ==============================================================================
if st.session_state.step == "UPLOAD":
    st.subheader("📋 Step 1: Upload Candidate Resume & Select Round")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Drop your resume file here (.pdf or .docx)", 
            type=["pdf", "docx"],
            help="Your resume will be parsed to generate custom architecture and language questions."
        )
        
    with col2:
        selected_round = st.radio(
            "Select Evaluation Round Mode:",
            options=["Technical Fundamentals", "Behavioral STAR Round"],
            help="Technical: Focuses on project design, DBMS/OS, and language mechanics.\nBehavioral: Assesses leadership and situation framing."
        )
        st.session_state.round_type = "Technical" if "Technical" in selected_round else "Behavioral"

    if uploaded_file is not None:
        if st.button("🚀 Initialize Interview Environment", type="primary", use_container_width=True):
            with st.spinner("Extracting resume data and generating 4-question matrix..."):
                try:
                    # 1. Parse uploaded resume binary bytes
                    file_bytes = uploaded_file.read()
                    st.session_state.resume_text = ResumeParsingEngine.process_file_stream(
                        uploaded_file.name, file_bytes
                    )
                    
                    # 2. Select prompt template based on round configuration
                    if st.session_state.round_type == "Technical":
                        prompt_template = MockInterviewPrompts.get_technical_generation_template()
                    else:
                        prompt_template = MockInterviewPrompts.get_behavioral_generation_template()
                        
                    # 3. Define primary (Gemini) and cross-cloud backup (Groq Llama) clients
                    primary_llm = llm_client.with_structured_output(QuestionGenerationMatrix)
                    backup_llm = ChatGroq(
                        model="llama-3.3-70b-versatile",
                        groq_api_key=EngineConfiguration().groq_key,
                        temperature=0.3
                    ).with_structured_output(QuestionGenerationMatrix)
                    
                    # Bind automatic fallback: switches to Groq instantly if Gemini encounters an error
                    structured_chain = prompt_template | primary_llm.with_fallbacks([backup_llm])
                    
                    response_matrix = structured_chain.invoke({"resume_text": st.session_state.resume_text})
                    
                    # 4. Save question payload array into session state
                    st.session_state.question_payload = response_matrix.questions
                    st.session_state.current_turn = 0
                    st.session_state.transcript = []
                    st.session_state.step = "INTERVIEW"
                    st.rerun()
                    
                except Exception as ex:
                    st.error(f"❌ Failed to process resume or generate questions: {str(ex)}")

# ==============================================================================
# PHASE 2: MULTI-TURN INTERVIEW LOOP (4 QUESTIONS)
# ==============================================================================
elif st.session_state.step == "INTERVIEW":
    turn_idx = st.session_state.current_turn
    total_turns = len(st.session_state.question_payload)
    
    # Check if all turns are finished
    if turn_idx >= total_turns:
        st.session_state.step = "DIAGNOSTICS"
        st.rerun()
        
    current_q = st.session_state.question_payload[turn_idx]
    
    # Display Progress Bar
    progress_val = (turn_idx) / total_turns
    st.progress(progress_val, text=f"Question {turn_idx + 1} of {total_turns} ({st.session_state.round_type} Round)")
    
    # Question Card Display
    st.info(f"**Target Evaluation Node:** {current_q.targeted_evaluation_node}")
    st.markdown(f"### ❓ Question {turn_idx + 1}: {current_q.question_text}")
    
    # Synthesize Audio via edge-tts
    audio_filename = f"q_{turn_idx + 1}.mp3"
    audio_file_path = os.path.join("static", "cache", audio_filename)
    
    if not os.path.exists(audio_file_path):
        with st.spinner("Synthesizing audio question..."):
            AudioOrchestrationEngine.synthesize_speech(current_q.question_text, audio_filename)
            
    if os.path.exists(audio_file_path):
        st.audio(audio_file_path, format="audio/mp3")

    st.markdown("---")
    st.subheader("🎙️ Your Response")
    
    # Tab selector for Voice Recording vs Text Fallback
    input_tab1, input_tab2 = st.tabs(["🎤 Voice Response (Microphone)", "⌨️ Text Response"])
    
    candidate_answer = ""
    
    with input_tab1:
        recorded_audio = st.audio_input("Record your answer below:")
        if recorded_audio is not None:
            with st.spinner("Transcribing audio via Groq Whisper LPU..."):
                try:
                    audio_bytes = recorded_audio.read()
                    candidate_answer = AudioOrchestrationEngine.transcribe_audio_stream(
                        audio_bytes, f"turn_{turn_idx + 1}.wav"
                    )
                    st.success("Transcription complete!")
                    st.write(f"**Transcribed Answer:** {candidate_answer}")
                except Exception as err:
                    st.error(f"Transcription error: {str(err)}")
                    
    with input_tab2:
        text_answer = st.text_area(
            "Or type your structured answer here:", 
            height=150, 
            key=f"text_input_{turn_idx}"
        )
        if text_answer.strip():
            candidate_answer = text_answer.strip()

    st.write("")
    if st.button("Submit Answer & Advance ➡️", type="primary"):
        if not candidate_answer.strip():
            st.warning("⚠️ Please provide a response (via voice or text) before advancing.")
        else:
            # Save interaction log into global session state transcript
            st.session_state.transcript.append({
                "question_id": current_q.question_id,
                "targeted_node": current_q.targeted_evaluation_node,
                "question": current_q.question_text,
                "answer": candidate_answer
            })
            st.session_state.current_turn += 1
            st.rerun()

# ==============================================================================
# PHASE 3: DIAGNOSTIC EVALUATION REPORT
# ==============================================================================
elif st.session_state.step == "DIAGNOSTICS":
    st.subheader("📊 Final Diagnostic Assessment Report")
    
    # Generate evaluation report once if not already present
    if st.session_state.diagnostic_report is None:
        with st.spinner("Auditing interview transcript and building diagnostic assessment..."):
            try:
                # Compile full transcript string log
                transcript_str = ""
                for entry in st.session_state.transcript:
                    transcript_str += f"Question [{entry['targeted_node']}]: {entry['question']}\n"
                    transcript_str += f"Candidate Answer: {entry['answer']}\n\n"
                    
                eval_template = MockInterviewPrompts.get_evaluation_template()
                
                # Define primary evaluator and Groq backup evaluator
                primary_evaluator = llm_client.with_structured_output(DiagnosticReportSchema)
                backup_evaluator = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    groq_api_key=EngineConfiguration().groq_key,
                    temperature=0.3
                ).with_structured_output(DiagnosticReportSchema)
                
                eval_chain = eval_template | primary_evaluator.with_fallbacks([backup_evaluator])
                
                st.session_state.diagnostic_report = eval_chain.invoke({"interview_transcript": transcript_str})
            except Exception as ex:
                st.error(f"❌ Failed to generate diagnostic report: {str(ex)}")
                st.stop()
                
    report = st.session_state.diagnostic_report
    
    if report:
        # Scorecard Section
        col_score, col_critique = st.columns([1, 2])
        
        with col_score:
            st.metric(label="Overall Candidate Score", value=f"{report.composite_score_out_of_10} / 10")
            st.markdown("#### Metric Breakdown")
            st.write(f"• **Technical Accuracy / Context:** {report.metric_breakdown.technical_accuracy_or_situation}/10")
            st.write(f"• **Communication Clarity:** {report.metric_breakdown.communication_clarity}/10")
            st.write(f"• **Complexity / STAR Action:** {report.metric_breakdown.complexity_awareness_or_action}/10")
            
        with col_critique:
            st.markdown("#### Performance Critique")
            st.info(report.overall_performance_critique)
            
        st.markdown("---")
        st.markdown("### 💡 Actionable Improvement Steps")
        for idx, feedback in enumerate(report.reconstructive_feedback, 1):
            st.markdown(f"**{idx}.** {feedback}")
            
        st.markdown("---")
        if st.button("🔄 Start New Interview Session", type="secondary"):
            st.session_state.step = "UPLOAD"
            st.session_state.resume_text = ""
            st.session_state.question_payload = []
            st.session_state.current_turn = 0
            st.session_state.transcript = []
            st.session_state.diagnostic_report = None
            st.rerun()