import io
from pypdf import PdfReader
from docx import Document

class ResumeParsingEngine:
    """Provides structural extractors for handling text conversion from binary document spaces."""
    
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """Parses a binary PDF byte stream into clean, sequential text lines."""
        text_accumulator = []
        # Wrap raw bytes into an in-memory binary stream layer
        binary_stream = io.BytesIO(file_bytes)
        pdf_reader = PdfReader(binary_stream)
        
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_accumulator.append(page_text)
                
        # Join pages and strip redundant vertical whitespaces
        combined_text = "\n".join(text_accumulator)
        return " ".join(combined_text.split())

    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        """Parses a binary Word Document byte array into compressed text structures."""
        binary_stream = io.BytesIO(file_bytes)
        document_object = Document(binary_stream)
        
        # Read text cleanly across all internal structural paragraph nodes
        paragraph_texts = [para.text for para in document_object.paragraphs if para.text.strip()]
        
        # Compress space arrays
        combined_text = "\n".join(paragraph_texts)
        return " ".join(combined_text.split())

    @classmethod
    def process_file_stream(cls, file_name: str, file_bytes: bytes) -> str:
        """Orchestrates file translation by evaluating incoming extensions natively."""
        lower_name = file_name.lower()
        
        if lower_name.endswith('.pdf'):
            return cls.extract_text_from_pdf(file_bytes)
        elif lower_name.endswith('.docx'):
            return cls.extract_text_from_docx(file_bytes)
        else:
            raise ValueError("❌ Unsupported File Type Error: The system only accepts valid '.pdf' or '.docx' formats.")

def run_local_parser_test():
    """Diagnostic check to verify that file stream readers compile data cleanly without exceptions."""
    print("\n📄 Initiating Document Parser Module Diagnostics...")
    print("-------------------------------------------------------")
    
    # 1. Create a simulated structural plain text payload
    mock_resume_content = (
        "Candidate: Alex Dev\n"
        "Skills: Python, FastAPI, PostgreSQL, Docker, Core OS, DBMS\n"
        "Project: Built a telemetry system using optimized SQL indexing frameworks."
    )
    
    try:
        # 2. Simulate compiling the text string into an in-memory mock DOCX array structure
        doc = Document()
        for line in mock_resume_content.split('\n'):
            doc.add_paragraph(line)
            
        mock_docx_bytes = io.BytesIO()
        doc.save(mock_docx_bytes)
        mock_docx_bytes.seek(0)
        
        # 3. Stream the byte buffer array back through our processor engine
        extracted_text = ResumeParsingEngine.process_file_stream("mock_resume.docx", mock_docx_bytes.read())
        print(f"✅ Parser Module Passed! Output String Array:\n   ↳ {extracted_text}\n")
        
    except Exception as error:
        print(f"❌ Document Parsing Test Failed: {str(error)}\n")

if __name__ == "__main__":
    run_local_parser_test()