from sentence_transformers import SentenceTransformer, util
import torch

# Load a lightweight, high-performance model suitable for semantic analysis
# 'all-MiniLM-L6-v2' is efficient and yields good results for paragraph similarity.
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_similarity_score(p1: str, p2: str):
    """Computes cosine similarity between two paragraphs."""
    embeddings = model.encode([p1, p2], convert_to_tensor=True)
    cosine_scores = util.cos_sim(embeddings[0], embeddings[1])
    return float(cosine_scores[0][0])

def analyze_semantic_meaning(p1: str, p2: str):
    """Determines if two paragraphs have the same semantic meaning."""
    score = get_similarity_score(p1, p2)
    
    # Heuristic for semantic meaning matching
    if score >= 0.85:
        match_level = "High Similarity / Same Meaning"
    elif score >= 0.65:
        match_level = "Moderate Similarity / Related Meaning"
    elif score >= 0.40:
        match_level = "Low Similarity / Potentially Related"
    else:
        match_level = "No Significant Semantic Relationship"
        
    return {
        "score": round(score, 4),
        "percentage": round(score * 100, 2),
        "match_level": match_level,
    }
