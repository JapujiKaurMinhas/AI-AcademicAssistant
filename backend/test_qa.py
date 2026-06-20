import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.utils.pdf_extractor import extract_text_from_pdf
from backend.utils.text_chunker import split_text_into_chunks
from backend.models.embeddings import create_embeddings, model
from backend.utils.vector_store import create_vector_store
from backend.utils.search import search_similar_chunks
from backend.utils.qa_engine import generate_answer

# Get absolute path for pdf
pdf_path = os.path.join(os.path.dirname(__file__), "uploads", "tisharesume.pdf")

print("\n--- Extracting PDF text ---")
text = extract_text_from_pdf(pdf_path)

print("Text length:", len(text))

print("\n--- Splitting text into chunks ---")
chunks = split_text_into_chunks(text)

print("Total chunks:", len(chunks))

print("\n--- Creating embeddings ---")
embeddings = create_embeddings(chunks)

print("Embeddings created:", len(embeddings))

print("\n--- Creating vector store ---")
index = create_vector_store(embeddings)

print("Vector store ready")

question = input("\nEnter your question: ")

question_embedding = model.encode([question])[0]

print("\n--- Searching relevant chunks ---")

results = search_similar_chunks(
    question_embedding,
    index,
    chunks
)

context = "\n".join(results)

print("\nContext found:")
print(context)

print("\n--- Generating AI answer ---")

answer = generate_answer(context, question)

print("\nAI Answer:")
print(answer)