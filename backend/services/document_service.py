import os
from PyPDF2 import PdfReader
from io import BytesIO

def extract_text_from_pdf(file_content: bytes):
    """Simple text extractor for PDF files."""
    try:
        reader = PdfReader(BytesIO(file_content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

# More advanced logic for large documents could include chunking and FAISS vector database
# but for a starter/final year project, extracting the full text or first 5000 chars is usually enough.
def get_pdf_summary(text: str, max_chars: int = 5000):
    return text[:max_chars]
