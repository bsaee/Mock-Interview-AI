# 🎯 AI Mock Engineering Interviewer

An end-to-end, decoupled AI-driven mock interview and technical assessment platform. The system ingests software engineering resumes, scrubs sensitive Personally Identifiable Information (PII), generates adaptive junior/entry-level interview questions via resilient multi-cloud LLM routing, captures voice responses via high-speed speech-to-text, and outputs structured diagnostic performance scorecards with optional ATS keyword alignment.

---

## 🏛️ System Architecture

The project follows a decoupled client-server architecture: a **FastAPI** backend service handles compute-heavy tasks, PII masking, and multi-cloud model orchestration, while an intuitive **Streamlit** frontend manages user interactions and session states.

\[ Candidate / Browser ]
         │
         ▼
[ Streamlit Client (app.py) ]  ──(HTTP / REST)──►  [ FastAPI Gateway (main.py) ]
                                                            │
                                  ┌─────────────────────────┼─────────────────────────┐
                                  ▼                         ▼                         ▼
                        [ PII Sanitizer ]         [ Multi-Cloud Router ]     [ Voice Pipeline ]
                        • Regex Tokenizer         • Gemini Flash (Primary)   • Groq Whisper STT
                        • [REDACTED_*] Tokens     • Groq Llama 3.3 (Failover)• edge-tts (TTS)
                                                            │
                                                            ▼
                                                [ Structured Evaluation ]
                                                • Pydantic Schemas
                                                • ATS Match & Scorecard
                                                • PDF/Markdown Reporter
\
---

## ⚡ Key Features

* **Client-Server REST Architecture:** Complete decoupling of UI presentation (\pp.py\) from business logic and inference engines (\main.py\) using OpenAPI/Swagger-documented endpoints.
* **Client-Side Data Privacy & PII Scrubbing:** Regex-driven redaction layer that cleans email addresses, telephone numbers, direct profile URLs (GitHub, LinkedIn), and postal codes before sending text to external LLM providers.
* **Cross-Cloud Resilient Fallback:** Primary reasoning runs on Google Gemini Flash, with automatic, zero-downtime failover to Groq-hosted Llama 3.3 (\llama-3.3-70b-versatile\) when handling rate limits or upstream 503 errors.
* **Calibrated Junior / Fresher Scope:** Questions target foundational programming paradigms, project implementation decisions, debugging logic, DBMS/OS basics, and STAR-method behavioral scenarios rather than senior-level system design.
* **Optional Role Targeting & ATS Match Engine:** Ingests optional Job Descriptions (via text paste or PDF/DOCX upload) to extract keyword overlap, surface missing competencies, and calculate estimated match percentages.
* **High-Throughput Speech Processing:** In-memory audio ingestion using Groq Whisper (\whisper-large-v3\) for sub-second speech-to-text transcription.
* **Exportable Performance Diagnostics:** Post-interview scoring out of 10, category metric breakdowns, and actionable tips downloadable as formatted **PDF** audit cards or plain **Markdown** files.

---

## 📂 Project Directory Structure

\\	ext
├── core/
│   ├── __init__.py
│   └── config.py              # Environment configuration & LLM client factories
├── parser/
│   ├── __init__.py
│   ├── document.py            # PDF/DOCX ingestion & PII redaction layer
│   └── audio.py               # Edge-TTS synthesis & Groq Whisper STT
├── pipeline/
│   ├── __init__.py
│   ├── templates.py           # Multi-agent prompt templates (Technical, Behavioral, ATS)
│   ├── evaluation.py          # Structured Pydantic contracts & schemas
│   └── reporter.py           # In-memory PDF (ReportLab) & Markdown report generators
├── app.py                     # Streamlit frontend application
├── main.py                    # FastAPI REST backend application
├── requirements.txt           # Python dependency manifest
├── .env.example               # Template for required environment variables
└── README.md
\
---

## 🛠️ Tech Stack

* **Backend & API:** FastAPI, Uvicorn, Pydantic v2
* **Frontend:** Streamlit, Custom CSS
* **LLM Orchestration:** LangChain Core, Google Generative AI, Groq SDK
* **Models:** Gemini Flash (\gemini-flash-latest\), Llama 3.3 70B (\llama-3.3-70b-versatile\), Groq Whisper (\whisper-large-v3\)
* **Document & Media Processing:** PyPDF, python-docx, edge-tts, ReportLab

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.10+ installed
* Google AI Studio API Key (\GEMINI_API_KEY\)
* Groq Cloud API Key (\GROQ_API_KEY\)

### 2. Clone & Setup Environment
\\ash
git clone https://github.com/your-username/mock-interview-ai.git
cd mock-interview-ai

python -m venv .venv
# On Windows:
.venv\Scriptsctivate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
\
### 3. Configure Environment Variables
Create a \.env\ file in the root directory:
\\env
GOOGLE_API_KEY=your_google_gemini_api_key
GROQ_API_KEY=your_groq_api_key
BACKEND_URL=http://127.0.0.1:8000
\
### 4. Run the Application

Start the **FastAPI backend** (Terminal 1):
\\ash
python -m uvicorn main:app --reload --port 8000
\*API interactive documentation will be available at \http://127.0.0.1:8000/docs\.*

Start the **Streamlit frontend** (Terminal 2):
\\ash
python -m streamlit run app.py
\*The web interface will launch at \http://localhost:8501\.*

---

## 📡 API Endpoint Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| \GET\ | \/api/health\ | Health check endpoint returning backend operational status. |
| \POST\ | \/api/resume/parse-and-sanitize\ | Ingests \.pdf\/\.docx\ files and returns text with PII redaction metrics. |
| \POST\ | \/api/interview/generate-questions\ | Produces an array of junior-calibrated interview questions. |
| \POST\ | \/api/audio/transcribe\ | Ingests raw audio buffer and transcribes speech using Groq Whisper. |
| \POST\ | \/api/interview/evaluate\ | Audits session transcript and outputs a structured diagnostic scorecard. |

---

## 🔒 Security & Privacy Notice

This application enforces an ephemeral data model:
* Resumes, job descriptions, audio recordings, and transcripts are processed exclusively in-memory during active sessions.
* Sensitive contact markers (emails, phone numbers, external URLs, postal addresses) are masked via regex tokens before being submitted to external LLM providers.
* No candidate data is written to permanent disk storage or shared relational databases.
