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

from utils.text_chunker import split_text_into_chunks

def get_pdf_summary(text: str, max_chars: int = 5000):
    """
    Chunk-level token-budgeted representation of large documents
    avoiding naive string slicing.
    """
    if len(text) <= max_chars:
        return text
    # Segment into coherent chunks and preserve leading sections within budget
    chunks = split_text_into_chunks(text, chunk_size=1000, overlap=100)
    selected = []
    total_len = 0
    for ch in chunks:
        if total_len + len(ch) <= max_chars:
            selected.append(ch)
            total_len += len(ch)
        else:
            break
    return "\n\n".join(selected) if selected else text[:max_chars]