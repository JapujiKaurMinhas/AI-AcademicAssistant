import time
import numpy as np
from typing import Dict, Any, List
from .search_space import SearchSpace
from .evaluation import RetrievalEvaluator
from .fitness import FitnessEvaluator

class SensitivityAnalyzer:
    """
    Executes real sensitivity sweeps over retrieval parameters and algorithm hyperparameters
    measuring actual changes in retrieval quality, latency, and token consumption.
    """
    def __init__(self, evaluator: RetrievalEvaluator, fitness_evaluator: FitnessEvaluator):
        self.evaluator = evaluator
        self.fitness = fitness_evaluator
        self.space = SearchSpace()

    def sweep_top_k(self, k_values: List[int] = None) -> List[Dict[str, Any]]:
        """Sweeps Top-K from 1 to 15 holding other parameters constant."""
        values = k_values or [1, 2, 3, 5, 7, 10, 15]
        default = self.space.get_default_vector()
        results = []

        for k in values:
            start = time.perf_counter()
            metrics = self.evaluator.evaluate_candidate(
                chunk_size=int(default[0]),
                chunk_overlap=int(default[1]),
                top_k=k,
                similarity_threshold=default[3],
                context_token_budget=int(default[4])
            )
            fit = self.fitness.evaluate(metrics)
            results.append({
                "top_k": k,
                "retrieval_quality": metrics["retrieval_quality"],
                "retrieval_relevance": metrics["retrieval_relevance"],
                "semantic_similarity": metrics["semantic_similarity"],
                "context_coverage": metrics["context_coverage"],
                "latency_ms": metrics["latency_ms"],
                "estimated_tokens": metrics["estimated_tokens"],
                "fitness": fit
            })
        return results

    def sweep_chunk_size(self, sizes: List[int] = None) -> List[Dict[str, Any]]:
        """Sweeps Chunk Size from 250 to 1400 holding other parameters constant."""
        values = sizes or [250, 400, 600, 800, 1000, 1200, 1400]
        default = self.space.get_default_vector()
        results = []

        for sz in values:
            overlap = int(sz * 0.15) # Maintain proportional overlap
            metrics = self.evaluator.evaluate_candidate(
                chunk_size=sz,
                chunk_overlap=overlap,
                top_k=int(default[2]),
                similarity_threshold=default[3],
                context_token_budget=int(default[4])
            )
            fit = self.fitness.evaluate(metrics)
            results.append({
                "chunk_size": sz,
                "chunk_overlap": overlap,
                "retrieval_quality": metrics["retrieval_quality"],
                "semantic_similarity": metrics["semantic_similarity"],
                "context_coverage": metrics["context_coverage"],
                "latency_ms": metrics["latency_ms"],
                "estimated_tokens": metrics["estimated_tokens"],
                "total_chunks": metrics["total_chunks_in_doc"],
                "fitness": fit
            })
        return results

    def sweep_similarity_threshold(self, thresholds: List[float] = None) -> List[Dict[str, Any]]:
        """Sweeps similarity threshold from 0.0 to 0.70."""
        values = thresholds or [0.0, 0.10, 0.20, 0.35, 0.50, 0.65]
        default = self.space.get_default_vector()
        results = []

        for th in values:
            metrics = self.evaluator.evaluate_candidate(
                chunk_size=int(default[0]),
                chunk_overlap=int(default[1]),
                top_k=int(default[2]),
                similarity_threshold=th,
                context_token_budget=int(default[4])
            )
            fit = self.fitness.evaluate(metrics)
            results.append({
                "similarity_threshold": th,
                "retrieval_quality": metrics["retrieval_quality"],
                "retrieval_relevance": metrics["retrieval_relevance"],
                "avg_retrieved_chunks": metrics["avg_retrieved_chunks"],
                "estimated_tokens": metrics["estimated_tokens"],
                "latency_ms": metrics["latency_ms"],
                "fitness": fit
            })
        return results

    def run_full_sensitivity(self) -> Dict[str, Any]:
        return {
            "top_k_sensitivity": self.sweep_top_k(),
            "chunk_size_sensitivity": self.sweep_chunk_size(),
            "threshold_sensitivity": self.sweep_similarity_threshold()
        }
