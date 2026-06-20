from sklearn.metrics.pairwise import cosine_similarity
from models.embeddings import get_embedding


def calculate_similarity(text1, text2):
    """
    Calculate semantic similarity between two texts
    """

    embedding1 = get_embedding(text1)
    embedding2 = get_embedding(text2)

    score = cosine_similarity(
        [embedding1],
        [embedding2]
    )[0][0]

    return float(score)