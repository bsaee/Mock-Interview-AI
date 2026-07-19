import os
import time
import asyncio
import edge_tts
from groq import Groq

class AudioOrchestrationEngine:
    """Handles low-latency local audio asset synthesis and cloud transcription pipelines."""
    
    @staticmethod
    def synthesize_speech(text_prompt: str, output_filename: str) -> str:
        """
        Transforms text question payloads into standard streamable MP3 files.
        Saves output locally within the static file server path.
        """
        # Ensure target cache subdirectory exists structurally
        cache_directory = os.path.join("static", "cache")
        os.makedirs(cache_directory, exist_ok=True)
        
        target_file_path = os.path.join(cache_directory, output_filename)
        
        # Select an articulate, modern English voice profile
        voice_profile = "en-US-AvaNeural"
        
        # Initialize edge-tts orchestration runner
        communicate = edge_tts.Communicate(text_prompt, voice_profile)
        
        # Execute the asynchronous text-to-speech engine inside a synchronous wrapper loop
        asyncio.run(communicate.save(target_file_path))
        
        return target_file_path

    @staticmethod
    def transcribe_audio_stream(audio_bytes: bytes, original_filename: str = "input_response.wav") -> str:
        """
        Caches raw microphone voice buffers to disk as binary chunks,
        then routes the binary object to the Groq Whisper execution layer for near-instant STT.
        """
        # Ensure target cache subdirectory exists structurally
        cache_directory = os.path.join("static", "cache")
        os.makedirs(cache_directory, exist_ok=True)
        
        # Create a unique file pointer using unix timestamp matrices to prevent file collisions
        unique_timestamp = int(time.time())
        temp_audio_path = os.path.join(cache_directory, f"{unique_timestamp}_{original_filename}")
        
        # Write the binary voice chunk payload down to disk safely
        with open(temp_audio_path, "wb") as audio_file:
            audio_file.write(audio_bytes)
            
        # Secure the API credential token directly from environment layers
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("❌ Missing Configuration Error: 'GROQ_API_KEY' environment variable not set.")
            
        # Initialize standard client connection bounds for Groq Cloud
        client = Groq(api_key=groq_api_key)
        
        try:
            # Stream the binary file handle up to Groq LPUs targeting Whisper Large V3
            with open(temp_audio_path, "rb") as file_handle:
                transcription_result = client.audio.transcriptions.create(
                    file=(temp_audio_path, file_handle.read()),
                    model="whisper-large-v3",
                    response_format="text"
                )
            
            # Clean up the local cached input file to keep disk footprint ultra-lightweight
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
                
            return str(transcription_result).strip()
            
        except Exception as system_error:
            # Gracefully clear cache even if transmission faults occur
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            raise RuntimeError(f"❌ Groq Audio Transcription Layer Failed: {str(system_error)}")

def run_local_audio_test():
    """Diagnostic suite confirming audio system loop capabilities."""
    print("\n🔊 Initiating Audio Pipeline Module Diagnostics...")
    print("-------------------------------------------------")
    
    test_question = "Explain how the Python Global Interpreter Lock manages standard multi-threading models."
    test_filename = "diagnostic_test.mp3"
    
    try:
        # 1. Test Text-to-Speech Engine
        print("🎙️ Testing Local TTS Synthesis Layer via edge-tts...")
        saved_path = AudioOrchestrationEngine.synthesize_speech(test_question, test_filename)
        print(f"   ↳ Success! Audio cached cleanly at: {saved_path}")
        
        # Clean up the generated file to keep workspace clean
        if os.path.exists(saved_path):
            os.remove(saved_path)
        print("✅ Milestone 4 Audio Core Verification Passed!\n")
        
    except Exception as error:
        print(f"❌ Audio Pipeline Verification Crashed: {str(error)}\n")

if __name__ == "__main__":
    run_local_audio_test()