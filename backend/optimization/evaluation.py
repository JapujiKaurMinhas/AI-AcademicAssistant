import time
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from utils.text_chunker import split_text_into_chunks, get_embedding_model

DEFAULT_BENCHMARK_DOCUMENT = """
Deep learning is a subset of machine learning, which is in turn a subset of artificial intelligence.
Artificial intelligence is a broad field that refers to any machine that can mimic human cognitive functions like learning and problem-solving.
Machine learning focuses on algorithms that learn from data without being explicitly programmed.
Deep learning extends this by using multi-layered artificial neural networks, typically referred to as deep neural networks, to model complex patterns in data.
In biological systems, learning is achieved through the modification of synaptic connections between neurons.
Artificial neural networks attempt to mimic this structure by using layers of mathematical nodes.
The input layer receives data, such as pixel values of an image or text characters.
The hidden layers perform non-linear transformations on the input using weights and biases that are adjusted during training.
The output layer provides the final prediction, such as classifying an image as a cat or dog.
Training a deep neural network requires a loss function and an optimization algorithm.
The loss function measures the difference between the network's prediction and the ground truth.
An example of a loss function is Mean Squared Error (MSE) for regression, or Cross-Entropy Loss for classification tasks.
The optimization algorithm, such as Stochastic Gradient Descent (SGD) or Adam, calculates the gradient of the loss function with respect to the network's weights.
These weights are then updated in the opposite direction of the gradient to minimize the loss.
This process of updating weights is called backpropagation.
Backpropagation applies the chain rule of calculus to calculate gradients layer by layer from the output back to the input.
Due to the high dimensionality of neural network parameter spaces, optimization can be challenging.
Networks can suffer from vanishing or exploding gradients, where gradients become too small or too large to update weights effectively.
Techniques such as batch normalization, residual connections, and careful weight initialization are used to stabilize training.
Transformer architectures utilize self-attention mechanisms to process sequential text data concurrently rather than recurrently.
Self-attention computes dynamic attention weights between all token pairs in a sequence, capturing long-range contextual dependencies.
Vector embeddings map high-dimensional categorical features or natural language text into dense continuous vector spaces where geometric proximity reflects semantic similarity.
Information retrieval systems leverage approximate nearest neighbor search over dense vector embeddings to retrieve relevant text passages for large language model generation.
"""

DEFAULT_BENCHMARK_QUERIES = [
    "What is the role of backpropagation and loss functions in training neural networks?",
    "How do transformer architectures and self-attention mechanisms capture semantic dependencies?",
    "What causes vanishing and exploding gradients and how can they be mitigated?",
    "How does dense vector retrieval find relevant text passages for large language models?"
]

def estimate_tokens(text: str) -> int:
    """Accurate token estimator for English academic text (~3.5 characters per token)."""
    if not text:
        return 0
    return int(len(text) / 3.5) + 5

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    dot = np.dot(v1, v2)
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 > 0 and n2 > 0:
        return float(dot / (n1 * n2))
    return 0.0


class RetrievalEvaluator:
    """
    Centralized Evaluation Engine for RAG document retrieval.
    Evaluates candidate retrieval parameters without expensive external LLM calls during search loops.
    Caches chunking and embedding structures to ensure maximum throughput on standard CPU systems.
    """
    def __init__(
        self,
        document_text: str = None,
        queries: List[str] = None,
        embedding_model = None
    ):
        self.text = (document_text or DEFAULT_BENCHMARK_DOCUMENT).strip()
        self.queries = queries or DEFAULT_BENCHMARK_QUERIES
        self.model = embedding_model or get_embedding_model()
        
        # Pre-encode queries once
        self.query_embeddings = [self.model.encode(q) for q in self.queries]
        
        # Internal caches:
        # 1. (chunk_size, chunk_overlap) -> (chunks_list, chunks_embeddings)
        self._chunk_cache: Dict[Tuple[int, int], Tuple[List[str], np.ndarray]] = {}
        # 2. (chunk_size, chunk_overlap, top_k, threshold, budget) -> evaluated_metrics_dict
        self._eval_cache: Dict[Tuple[int, int, int, float, int], Dict[str, Any]] = {}

    def get_or_create_chunks(self, chunk_size: int, chunk_overlap: int) -> Tuple[List[str], np.ndarray]:
        key = (int(chunk_size), int(chunk_overlap))
        if key in self._chunk_cache:
            return self._chunk_cache[key]

        # Use the application's real chunking engine
        chunks = split_text_into_chunks(self.text, chunk_size=chunk_size, overlap=chunk_overlap)
        if not chunks:
            chunks = [self.text[:chunk_size]] if self.text else ["Empty document"]

        # Vectorize chunks
        embeddings = self.model.encode(chunks, show_progress_bar=False)
        self._chunk_cache[key] = (chunks, embeddings)
        return chunks, embeddings

    def evaluate_candidate(
        self,
        chunk_size: int,
        chunk_overlap: int,
        top_k: int,
        similarity_threshold: float,
        context_token_budget: int
    ) -> Dict[str, Any]:
        """
        Executes real vector retrieval for the candidate parameters and computes measurable metrics.
        """
        cache_key = (
            int(chunk_size),
            int(chunk_overlap),
            int(top_k),
            round(float(similarity_threshold), 3),
            int(context_token_budget)
        )
        if cache_key in self._eval_cache:
            res = dict(self._eval_cache[cache_key])
            res["cached"] = True
            return res

        start_time = time.perf_counter()
        
        # 1. Segment text and retrieve embeddings
        chunks, chunk_embs = self.get_or_create_chunks(chunk_size, chunk_overlap)
        total_chunks = len(chunks)

        all_query_relevances = []
        all_query_semantic_sims = []
        all_query_coverages = []
        all_retrieved_tokens = []
        all_retrieved_counts = []
        sample_retrieved_snippets = []

        # 2. For each academic benchmark query, run vector retrieval
        for q_idx, (query, q_emb) in enumerate(zip(self.queries, self.query_embeddings)):
            # Compute cosine similarities
            sims = [cosine_similarity(q_emb, c_emb) for c_emb in chunk_embs]
            
            # Filter and rank
            ranked_indices = np.argsort(sims)[::-1]
            
            selected_chunks = []
            selected_sims = []
            current_tokens = 0

            for idx in ranked_indices:
                if len(selected_chunks) >= top_k:
                    break
                sim = sims[idx]
                if sim < similarity_threshold:
                    continue
                
                chunk_text = chunks[idx]
                chunk_tokens = estimate_tokens(chunk_text)
                
                # Check context budget constraint
                if current_tokens + chunk_tokens > context_token_budget:
                    # If first chunk itself exceeds budget, we allow at least a truncated portion
                    if len(selected_chunks) == 0:
                        selected_chunks.append(chunk_text)
                        selected_sims.append(sim)
                        current_tokens += chunk_tokens
                    break
                
                selected_chunks.append(chunk_text)
                selected_sims.append(sim)
                current_tokens += chunk_tokens

            # Metric: Retrieval Relevance (Mean similarity of retrieved chunks)
            q_relevance = float(np.mean(selected_sims)) if selected_sims else 0.0
            # Metric: Semantic Similarity (Max similarity of top-1 chunk)
            q_semantic = float(selected_sims[0]) if selected_sims else 0.0
            
            # Metric: Context Coverage / Non-redundancy
            # Measures diversity between retrieved chunks so we don't return 5 identical chunks
            if len(selected_chunks) > 1:
                chunk_indices = [ranked_indices[i] for i in range(len(selected_chunks))]
                pairwise_sims = []
                for i in range(len(chunk_indices)):
                    for j in range(i + 1, len(chunk_indices)):
                        p_sim = cosine_similarity(chunk_embs[chunk_indices[i]], chunk_embs[chunk_indices[j]])
                        pairwise_sims.append(p_sim)
                mean_pairwise = float(np.mean(pairwise_sims)) if pairwise_sims else 0.0
                # Higher diversity = lower pairwise similarity
                coverage = max(0.0, 1.0 - mean_pairwise)
            else:
                coverage = 1.0 if selected_chunks else 0.0

            all_query_relevances.append(q_relevance)
            all_query_semantic_sims.append(q_semantic)
            all_query_coverages.append(coverage)
            all_retrieved_tokens.append(current_tokens)
            all_retrieved_counts.append(len(selected_chunks))

            if q_idx == 0:
                sample_retrieved_snippets = [c[:180] + ("..." if len(c) > 180 else "") for c in selected_chunks]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        mean_relevance = round(float(np.mean(all_query_relevances)), 4)
        mean_semantic = round(float(np.mean(all_query_semantic_sims)), 4)
        mean_coverage = round(float(np.mean(all_query_coverages)), 4)
        avg_tokens = int(np.mean(all_retrieved_tokens))
        avg_count = round(float(np.mean(all_retrieved_counts)), 1)
        composite_quality = round((mean_relevance * 0.5 + mean_semantic * 0.3 + mean_coverage * 0.2), 4)

        result = {
            "retrieval_relevance": mean_relevance,
            "semantic_similarity": mean_semantic,
            "context_coverage": mean_coverage,
            "retrieval_quality": composite_quality,
            "latency_ms": round(elapsed_ms, 2),
            "estimated_tokens": avg_tokens,
            "avg_retrieved_chunks": avg_count,
            "total_chunks_in_doc": total_chunks,
            "sample_snippets": sample_retrieved_snippets[:3],
            "cached": False
        }

        self._eval_cache[cache_key] = result
        return result
