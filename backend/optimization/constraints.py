from typing import List, Dict, Any, Tuple
from .search_space import SearchSpace

class ConstraintHandler:
    """
    Validates, repairs, and computes penalty values for retrieval parameter candidates.
    Constraints:
        C1: chunk_overlap < chunk_size (strict physical chunking requirement)
        C2: chunk_overlap <= 0.5 * chunk_size (sensible overlap ceiling to prevent redundancy)
        C3: top_k >= 1
        C4: context_token_budget <= 6000
        C5: estimated_tokens <= context_token_budget
        C6: parameter values within defined bounds
        C7 (optional): retrieval_latency <= max_allowed_latency
    """
    def __init__(self, search_space: SearchSpace, max_latency_ms: float = 2000.0):
        self.space = search_space
        self.max_latency_ms = max_latency_ms

    def validate(self, vec: List[float], metrics: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
        violations = []
        param_dict = self.space.to_dict(vec)
        
        chunk_size = param_dict["chunk_size"]
        chunk_overlap = param_dict["chunk_overlap"]
        top_k = param_dict["top_k"]
        threshold = param_dict["similarity_threshold"]
        budget = param_dict["context_token_budget"]

        # C1 & C2: Overlap constraints
        if chunk_overlap >= chunk_size:
            violations.append(f"Overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})")
        elif chunk_overlap > 0.5 * chunk_size:
            violations.append(f"Overlap ({chunk_overlap}) exceeds 50% of chunk_size ({chunk_size})")

        # C3: Top-K
        if top_k < 1:
            violations.append(f"Top-K ({top_k}) must be at least 1")

        # C4: Budget bounds
        if budget > 6000 or budget < 500:
            violations.append(f"Token budget ({budget}) outside permissible [500, 6000]")

        # C6: Bounds check
        for param in self.space.parameters:
            val = param_dict[param.name]
            if val < param.lower - 1e-4 or val > param.upper + 1e-4:
                violations.append(f"Parameter '{param.name}'={val} outside bounds [{param.lower}, {param.upper}]")

        # Dynamic constraints evaluated if metrics are available
        if metrics:
            tokens_used = metrics.get("estimated_tokens", 0)
            if tokens_used > budget:
                violations.append(f"Retrieved context tokens ({tokens_used}) exceeds configured budget ({budget})")

            latency_ms = metrics.get("latency_ms", 0.0)
            if self.max_latency_ms and latency_ms > self.max_latency_ms:
                violations.append(f"Retrieval latency ({latency_ms:.1f}ms) exceeds max ceiling ({self.max_latency_ms}ms)")

        return len(violations) == 0, violations

    def repair(self, vec: List[float]) -> List[float]:
        """Repairs a candidate solution vector to strictly satisfy structural constraints."""
        repaired = list(vec)
        param_dict = self.space.to_dict(repaired)
        
        chunk_size = param_dict["chunk_size"]
        chunk_overlap = param_dict["chunk_overlap"]

        # Clamp to bounds first
        repaired = self.space.clamp_vector(repaired)
        param_dict = self.space.to_dict(repaired)
        chunk_size = param_dict["chunk_size"]
        chunk_overlap = param_dict["chunk_overlap"]

        # If overlap >= 0.5 * chunk_size, repair it
        if chunk_overlap >= 0.5 * chunk_size:
            repaired[1] = float(max(0, int(chunk_size * 0.25)))

        # Ensure top_k >= 1
        if repaired[2] < 1:
            repaired[2] = 1.0

        return self.space.clamp_vector(repaired)

    def compute_penalty(self, vec: List[float], metrics: Dict[str, Any] = None) -> float:
        """Computes quadratic penalty for constraint violations."""
        penalty = 0.0
        param_dict = self.space.to_dict(vec)
        
        chunk_size = param_dict["chunk_size"]
        chunk_overlap = param_dict["chunk_overlap"]

        if chunk_overlap >= 0.5 * chunk_size:
            excess = chunk_overlap - (0.5 * chunk_size)
            penalty += 0.5 * (excess / (chunk_size + 1e-5)) ** 2

        if metrics:
            budget = param_dict["context_token_budget"]
            tokens_used = metrics.get("estimated_tokens", 0)
            if tokens_used > budget:
                over_ratio = (tokens_used - budget) / budget
                penalty += 1.0 * (over_ratio ** 2)

            latency_ms = metrics.get("latency_ms", 0.0)
            if self.max_latency_ms and latency_ms > self.max_latency_ms:
                over_latency = (latency_ms - self.max_latency_ms) / self.max_latency_ms
                penalty += 0.5 * (over_latency ** 2)

        return penalty
