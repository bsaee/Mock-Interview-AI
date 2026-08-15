import io
import re
from typing import Tuple, Dict
from pypdf import PdfReader
from docx import Document

class PIISanitizer:
    """Detects and redacts sensitive Personally Identifiable Information (PII) from raw text."""

    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    )
    PHONE_PATTERN = re.compile(
        r'(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{3,5}[-.\s]?\d{3,5}\b'
    )
    URL_PATTERN = re.compile(
        r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
        r'|www\.[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
        r'|(?:linkedin\.com|github\.com)/[-a-zA-Z0-9_./]+'
    )
    POSTAL_CODE_PATTERN = re.compile(
        r'\b\d{5}(?:[-\s]\d{4})?\b|\b\d{6}\b'
    )

    @classmethod
    def sanitize(cls, raw_text: str) -> Tuple[str, Dict[str, int]]:
        """
        Scrubs emails, phone numbers, URLs, and postal codes.
        Returns the sanitized text string along with a redaction audit counter.
        """
        audit_counts = {
            "emails_redacted": 0,
            "phones_redacted": 0,
            "urls_redacted": 0,
            "locations_redacted": 0
        }

        # 1. Redact URLs and Profiles
        raw_text, count = cls.URL_PATTERN.subn("[REDACTED_URL]", raw_text)
        audit_counts["urls_redacted"] = count

        # 2. Redact Emails
        raw_text, count = cls.EMAIL_PATTERN.subn("[REDACTED_EMAIL]", raw_text)
        audit_counts["emails_redacted"] = count

        # 3. Redact Phone Numbers
        raw_text, count = cls.PHONE_PATTERN.subn("[REDACTED_PHONE]", raw_text)
        audit_counts["phones_redacted"] = count

        # 4. Redact Zip/Postal Codes
        raw_text, count = cls.POSTAL_CODE_PATTERN.subn("[REDACTED_LOCATION]", raw_text)
        audit_counts["locations_redacted"] = count

        # Normalize whitespace after redaction
        clean_text = " ".join(raw_text.split())
        return clean_text, audit_counts


class ResumeParsingEngine:
    """Provides structural extractors for converting binary document streams to sanitized text."""
    
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """Parses a binary PDF byte stream into raw text lines."""
        text_accumulator = []
        binary_stream = io.BytesIO(file_bytes)
        pdf_reader = PdfReader(binary_stream)
        
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_accumulator.append(page_text)
                
        return " ".join("\n".join(text_accumulator).split())

    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        """Parses a binary Word Document byte array into raw text."""
        binary_stream = io.BytesIO(file_bytes)
        document_object = Document(binary_stream)
        
        paragraph_texts = [para.text for para in document_object.paragraphs if para.text.strip()]
        return " ".join("\n".join(paragraph_texts).split())

    @classmethod
    def process_file_stream(cls, file_name: str, file_bytes: bytes, sanitize: bool = True) -> Tuple[str, Dict[str, int]]:
        """
        Orchestrates file extraction and executes automatic PII sanitization.
        Returns: (sanitized_text, redaction_metrics)
        """
        lower_name = file_name.lower()
        
        if lower_name.endswith('.pdf'):
            extracted_text = cls.extract_text_from_pdf(file_bytes)
        elif lower_name.endswith('.docx'):
            extracted_text = cls.extract_text_from_docx(file_bytes)
        else:
            raise ValueError("❌ Unsupported File Type: Only '.pdf' and '.docx' are accepted.")

        if sanitize:
            return PIISanitizer.sanitize(extracted_text)
        
        return extracted_text, {}


if __name__ == "__main__":
    print("\n🔒 Testing PII Sanitizer & Document Parser Module...")
    print("-------------------------------------------------------")
    
    sample_resume = (
        "John Doe | Email: john.doe@techcorp.io | Phone: +1 (555) 234-5678\n"
        "Location: San Francisco, CA 94105 | LinkedIn: linkedin.com/in/johndoe | GitHub: github.com/johndoe\n"
        "Experience: Built high-throughput API endpoints using FastAPI and PostgreSQL."
    )
    
    clean_text, audit = PIISanitizer.sanitize(sample_resume)
    print("Sanitized Output:\n↳", clean_text)
    print("\nRedaction Audit Log:\n↳", audit)
    print("\n✅ PII Redaction Layer Operational!\n")