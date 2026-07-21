import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

class EngineConfiguration:
    """Manages system environment variable validation and initializes API wrappers."""
    
    def __init__(self):
        # Programmatically read local environment mappings
        self.google_key = os.environ.get("GOOGLE_API_KEY")
        self.groq_key = os.environ.get("GROQ_API_KEY")
        
        # Enforce strict build boundaries before running downstream application services
        if not self.google_key:
            raise ValueError("❌ Missing Environment Error: 'GOOGLE_API_KEY' is not set in the active shell layer.")
        if not self.groq_key:
            raise ValueError("❌ Missing Environment Error: 'GROQ_API_KEY' is not set in the active shell layer.")

    def get_llm_client(self) -> ChatGoogleGenerativeAI:
        """Initializes the central text reasoning intelligence engine via Google Gemini."""
        return ChatGoogleGenerativeAI(
            model="gemini-flash-latest", 
            google_api_key=self.google_key,
            temperature=0.3,
            max_retries=3
        )

    def get_transcription_client(self) -> ChatGroq:
        """Initializes the ultra-fast speech-to-text pipeline connection layer via Groq."""
        return ChatGroq(
            model="llama-3.1-8b-instant", 
            groq_api_key=self.groq_key
        )

def parse_response_content(response) -> str:
    """Safely extracts text content from LangChain response objects, handling both strings and lists."""
    content = getattr(response, "content", "")
    if isinstance(content, list):
        # Extract text elements if the model returns an array of content blocks
        text_blocks = [block.get("text", "") if isinstance(block, dict) else str(block) for block in content]
        return "".join(text_blocks).strip()
    return str(content).strip()

def verify_system_gateways():
    """Executes a diagnostic integration test against both remote cloud microservices."""
    print("\n🚀 Initiating System Integration Gateway Tests...")
    print("-------------------------------------------------")
    
    try:
        config = EngineConfiguration()
        
        # 1. Validate Gemini Gateway Connection
        print("🤖 Contacting Google Gemini 3.5 Flash Gateway...")
        gemini_client = config.get_llm_client()
        gemini_response = gemini_client.invoke("Confirm connection by printing exactly: GEMINI_ONLINE")
        gemini_text = parse_response_content(gemini_response)
        print(f"   ↳ Response Received: {gemini_text}")
        
        # 2. Validate Groq/Whisper Infrastructure Gateway Connection
        print("⚡ Contacting Groq Cloud LPU Framework...")
        groq_client = config.get_transcription_client()
        groq_response = groq_client.invoke("Confirm connection by printing exactly: GROQ_ONLINE")
        groq_text = parse_response_content(groq_response)
        print(f"   ↳ Response Received: {groq_text}\n")
        
        print("✅ Milestone 1 Verification Passed: Both cloud dependencies are fully operational!")
        
    except Exception as error:
        print(f"\n❌ Gateway Connection Diagnostic Failed: {str(error)}")
        print("👉 Double check your keys inside the .env file and ensure your active terminal has executed 'source .venv/bin/activate'.\n")

if __name__ == "__main__":
    verify_system_gateways()