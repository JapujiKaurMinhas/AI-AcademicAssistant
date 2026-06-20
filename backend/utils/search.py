import numpy as np

def search_similar_chunks(question_embedding, index, chunks, k=3):

    D, I = index.search(np.array([question_embedding]), k)

    results = [chunks[i] for i in I[0]]

    return results