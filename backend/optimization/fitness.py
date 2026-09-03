from typing import Dict, Any, List
from dataclasses import dataclass, asdict

@dataclass
class FitnessWeights:
    w_retrieval: float = 0.35      # Weight for retrieval relevance (cosine similarity)
    w_semantic: float = 0.25       # Weight for query-context semantic alignment
    w_coverage: float = 0.15       # Weight for chunk diversity / non-redundancy
    w_latency: float = 0.15        # Penalty weight for normalized latency
    w_tokens: float = 0.10         # Penalty weight for normalized token usage

    def normalize(self):
        total = self.w_retrieval + self.w_semantic + self.w_coverage + self.w_latency + self.w_tokens
        if total > 0:
            self.w_retrieval /= total
            self.w_semantic /= total
            self.w_coverage /= total
            self.w_latency /= total
            self.w_tokens /= total

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


class FitnessEvaluator:
    """
    Computes fitness scores and multi-objective vectors from raw retrieval metrics.
    Fitness(X) = w1 * RetrievalRelevance + w2 * SemanticSim + w3 * Coverage
                 - w4 * NormLatency - w5 * NormTokens - ConstraintPenalty
    """
    def __init__(self, weights: FitnessWeights = None, max_ref_latency_ms: float = 150.0, max_ref_tokens: int = 4000):
        self.weights = weights or FitnessWeights()
        self.max_ref_latency_ms = max_ref_latency_ms
        self.max_ref_tokens = max_ref_tokens

    def evaluate(self, metrics: Dict[str, Any], penalty: float = 0.0) -> float:
        retrieval_sim = float(metrics.get("retrieval_relevance", 0.0))    # 0.0 - 1.0
        semantic_sim = float(metrics.get("semantic_similarity", 0.0))     # 0.0 - 1.0
        coverage = float(metrics.get("context_coverage", 0.0))             # 0.0 - 1.0
        
        latency_ms = float(metrics.get("latency_ms", 0.0))
        norm_latency = min(1.0, latency_ms / max(1.0, self.max_ref_latency_ms))
        
        tokens = float(metrics.get("estimated_tokens", 0))
        norm_tokens = min(1.0, tokens / max(1.0, self.max_ref_tokens))

        raw_fitness = (
            self.weights.w_retrieval * retrieval_sim +
            self.weights.w_semantic * semantic_sim +
            self.weights.w_coverage * coverage -
            self.weights.w_latency * norm_latency -
            self.weights.w_tokens * norm_tokens
        )
        
        final_fitness = raw_fitness - penalty
        return round(float(final_fitness), 5)

    def evaluate_multi_objective(self, metrics: Dict[str, Any]) -> List[float]:
        """
        Returns objective values for NSGA-II.
        Convention: NSGA-II minimizes all objectives.
        Obj 1: Quality (negated to minimize: -1 * (retrieval + semantic + coverage))
        Obj 2: Latency (minimize latency_ms)
        Obj 3: Token cost (minimize estimated_tokens)
        """
        retrieval_sim = float(metrics.get("retrieval_relevance", 0.0))
        semantic_sim = float(metrics.get("semantic_similarity", 0.0))
        coverage = float(metrics.get("context_coverage", 0.0))
        quality = (retrieval_sim * 0.45 + semantic_sim * 0.35 + coverage * 0.20)
        
        obj1 = -1.0 * quality                      # Minimize negative quality (equivalent to maximizing quality)
        obj2 = float(metrics.get("latency_ms", 0.0)) # Minimize latency (ms)
        obj3 = float(metrics.get("estimated_tokens", 0.0)) # Minimize tokens
        
        return [round(obj1, 5), round(obj2, 3), round(obj3, 1)]
