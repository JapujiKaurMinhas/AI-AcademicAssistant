from sentence_transformers import SentenceTransformer

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

def create_embeddings(text_chunks):
    """
    Convert text chunks into embeddings.
    """
    embeddings = model.encode(text_chunks)
    return embeddings

def get_embedding(text):
    """
    Convert a single text string into an embedding.
    """
    return model.encode(text)