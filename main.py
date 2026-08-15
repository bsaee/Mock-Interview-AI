import os
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langchain_groq import ChatGroq
from core.config import EngineConfiguration
from parser.document import ResumeParsingEngine
from parser.audio import AudioOrchestrationEngine
from pipeline.templates import MockInterviewPrompts
from pipeline.evaluation import (
    QuestionGenerationMatrix,
    DiagnosticReportSchema
)
from pipeline.reporter import ReportGenerator

# Initialize FastAPI application
app = FastAPI(
    title="AI Mock Interviewer Backend Service",
    description="REST API service for PII-sanitized resume processing, dynamic question generation, STT/TTS audio pipelines, and diagnostic evaluations.",
    version="1.0.0"
)

# Enable CORS for local/cloud frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine configuration
config = EngineConfiguration()
llm_client = config.get_llm_client()

# --- Request / Response Pydantic Models for the API ---
class GenerateQuestionsRequest(BaseModel):
    resume_text: str
    round_type: str = "Technical"  # "Technical" or "Behavioral"
    target_role: Optional[str] = "Entry-Level / Junior Software Engineer"
    job_description: Optional[str] = "General Software Development Fundamentals"
    num_questions: int = 4

class EvaluationRequest(BaseModel):
    transcript: List[Dict[str, Any]]
    target_role: Optional[str] = ""
    job_description: Optional[str] = ""
    resume_text: str = ""

# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint to verify backend service status."""
    return {"status": "healthy", "service": "AI Mock Interview Engine"}


@app.post("/api/resume/parse-and-sanitize")
async def parse_and_sanitize_resume(file: UploadFile = File(...)):
    """
    Accepts .pdf or .docx resume binary upload, extracts text,
    and applies regex PII sanitization.
    """
    try:
        file_bytes = await file.read()
        clean_text, audit_counts = ResumeParsingEngine.process_file_stream(
            file_name=file.filename,
            file_bytes=file_bytes,
            sanitize=True
        )
        return {
            "filename": file.filename,
            "sanitized_resume_text": clean_text,
            "redaction_audit": audit_counts
        }
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f"Resume processing failed: {str(ex)}")


@app.post("/api/interview/generate-questions", response_model=QuestionGenerationMatrix)
async def generate_questions(payload: GenerateQuestionsRequest):
    """
    Generates structured interview questions calibrated for Junior/Fresher level
    using Gemini Flash with an automatic Groq Llama 3.3 failover.
    """
    try:
        # 1. Select prompt blueprint
        if payload.round_type == "Technical":
            prompt_template = MockInterviewPrompts.get_technical_generation_template()
        else:
            prompt_template = MockInterviewPrompts.get_behavioral_generation_template()

        # 2. Configure primary LLM and cross-cloud backup LLM
        primary_llm = llm_client.with_structured_output(QuestionGenerationMatrix)
        backup_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=config.groq_key,
            temperature=0.3
        ).with_structured_output(QuestionGenerationMatrix)

        chain = prompt_template | primary_llm.with_fallbacks([backup_llm])

        # 3. Invoke LLM chain
        response_matrix = chain.invoke({
            "resume_text": payload.resume_text,
            "target_role": payload.target_role or "Entry-Level / Junior Software Engineer",
            "job_description": payload.job_description or "General Software Development Fundamentals",
            "num_questions": payload.num_questions
        })

        return response_matrix

    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(ex)}")


@app.post("/api/audio/transcribe")
async def transcribe_candidate_audio(file: UploadFile = File(...)):
    """
    Transcribes uploaded audio buffer (.wav/.mp3) to text via Groq Whisper.
    """
    try:
        audio_bytes = await file.read()
        transcription = AudioOrchestrationEngine.transcribe_audio_stream(
            audio_bytes=audio_bytes,
            original_filename=file.filename or "input.wav"
        )
        return {"transcription": transcription}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Audio transcription failed: {str(ex)}")


@app.post("/api/interview/evaluate", response_model=DiagnosticReportSchema)
async def evaluate_interview_session(payload: EvaluationRequest):
    """
    Analyzes candidate multi-turn transcript and generates a structured
    diagnostic report (with optional ATS scoring).
    """
    try:
        has_ats = bool(payload.target_role or payload.job_description)
        
        # Compile transcript into single string block
        transcript_str = ""
        for entry in payload.transcript:
            node = entry.get("targeted_node", "N/A")
            question = entry.get("question", "")
            answer = entry.get("answer", "")
            transcript_str += f"Question [{node}]: {question}\nCandidate Answer: {answer}\n\n"

        eval_template = MockInterviewPrompts.get_evaluation_template(include_ats=has_ats)

        primary_evaluator = llm_client.with_structured_output(DiagnosticReportSchema)
        backup_evaluator = ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=config.groq_key,
            temperature=0.3
        ).with_structured_output(DiagnosticReportSchema)

        eval_chain = eval_template | primary_evaluator.with_fallbacks([backup_evaluator])

        diagnostic_report = eval_chain.invoke({
            "interview_transcript": transcript_str,
            "target_role": payload.target_role or "N/A",
            "job_description": payload.job_description or "N/A",
            "resume_text": payload.resume_text
        })

        return diagnostic_report

    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Diagnostic evaluation failed: {str(ex)}")