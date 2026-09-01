from utils.pdf_extractor import extract_text_from_pdf
from utils.text_chunker import split_text_into_chunks
from models.embeddings import create_embeddings, model
from utils.vector_store import create_vector_store
from utils.search import search_similar_chunks
from utils.qa_engine import generate_answer
from services.analytics_service import log_event

chunks = None
index = None

def process_pdf(pdf_path):

    global chunks, index

    log_event("upload", {"file": pdf_path})

    text = extract_text_from_pdf(pdf_path)

    chunks = split_text_into_chunks(text)

    embeddings = create_embeddings(chunks)

    index = create_vector_store(embeddings)


def answer_question(question):

    log_event("question", {"query": question})

    question_embedding = model.encode([question])[0]

    results = search_similar_chunks(
        question_embedding,
        index,
        chunks
    )

    context = "\n".join(results)

    answer = generate_answer(context, question)

    return answer