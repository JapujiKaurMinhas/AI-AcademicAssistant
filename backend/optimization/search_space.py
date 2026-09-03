import random
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict

@dataclass
class ParameterSpec:
    name: str
    lower: float
    upper: float
    is_integer: bool = True
    default: float = 0.0
    description: str = ""

    def clamp(self, value: float) -> float:
        val = max(self.lower, min(self.upper, value))
        if self.is_integer:
            return round(val)
        return float(round(val, 4))

    def sample(self) -> float:
        if self.is_integer:
            return random.randint(int(self.lower), int(self.upper))
        return round(random.uniform(self.lower, self.upper), 4)

    def normalize(self, value: float) -> float:
        if self.upper == self.lower:
            return 0.0
        return (value - self.lower) / (self.upper - self.lower)

    def denormalize(self, norm_val: float) -> float:
        clamped_norm = max(0.0, min(1.0, norm_val))
        val = self.lower + clamped_norm * (self.upper - self.lower)
        return self.clamp(val)


class SearchSpace:
    """
    Defines the multidimensional decision space for RAG retrieval parameter optimization.
    Decision vector:
        X = [chunk_size, chunk_overlap, top_k, similarity_threshold, context_token_budget]
    """
    def __init__(self, custom_bounds: Dict[str, Tuple[float, float]] = None):
        bounds = custom_bounds or {}
        
        self.parameters: List[ParameterSpec] = [
            ParameterSpec(
                name="chunk_size",
                lower=bounds.get("chunk_size", (200, 1500))[0],
                upper=bounds.get("chunk_size", (200, 1500))[1],
                is_integer=True,
                default=800,
                description="Text chunk size in characters for document segmentation."
            ),
            ParameterSpec(
                name="chunk_overlap",
                lower=bounds.get("chunk_overlap", (0, 300))[0],
                upper=bounds.get("chunk_overlap", (0, 300))[1],
                is_integer=True,
                default=100,
                description="Character overlap between consecutive chunks to retain contextual boundaries."
            ),
            ParameterSpec(
                name="top_k",
                lower=bounds.get("top_k", (1, 20))[0],
                upper=bounds.get("top_k", (1, 20))[1],
                is_integer=True,
                default=3,
                description="Number of top ranked candidate chunks retrieved from the vector index."
            ),
            ParameterSpec(
                name="similarity_threshold",
                lower=bounds.get("similarity_threshold", (0.0, 1.0))[0],
                upper=bounds.get("similarity_threshold", (0.0, 1.0))[1],
                is_integer=False,
                default=0.20,
                description="Minimum cosine similarity cutoff for including retrieved chunks."
            ),
            ParameterSpec(
                name="context_token_budget",
                lower=bounds.get("context_token_budget", (500, 6000))[0],
                upper=bounds.get("context_token_budget", (500, 6000))[1],
                is_integer=True,
                default=3000,
                description="Maximum total token ceiling allowed in the assembled prompt context."
            ),
        ]
        self._param_map = {p.name: p for p in self.parameters}

    @property
    def dimension(self) -> int:
        return len(self.parameters)

    @property
    def names(self) -> List[str]:
        return [p.name for p in self.parameters]

    def get_default_vector(self) -> List[float]:
        return [p.default for p in self.parameters]

    def sample_vector(self) -> List[float]:
        vec = [p.sample() for p in self.parameters]
        # Ensure chunk_overlap < chunk_size at sampling
        if vec[1] >= vec[0]:
            vec[1] = max(0, int(vec[0] * 0.25))
        return vec

    def clamp_vector(self, vec: List[float]) -> List[float]:
        clamped = [p.clamp(v) for p, v in zip(self.parameters, vec)]
        # Enforce basic overlap integrity
        if clamped[1] >= clamped[0]:
            clamped[1] = max(0, int(clamped[0] * 0.5))
        return clamped

    def normalize_vector(self, vec: List[float]) -> List[float]:
        return [p.normalize(v) for p, v in zip(self.parameters, vec)]

    def denormalize_vector(self, norm_vec: List[float]) -> List[float]:
        return self.clamp_vector([p.denormalize(nv) for p, nv in zip(self.parameters, norm_vec)])

    def to_dict(self, vec: List[float]) -> Dict[str, Any]:
        return {p.name: (int(v) if p.is_integer else round(float(v), 4)) 
                for p, v in zip(self.parameters, vec)}

    def from_dict(self, d: Dict[str, Any]) -> List[float]:
        return [float(d.get(p.name, p.default)) for p in self.parameters]

    def get_specification(self) -> List[Dict[str, Any]]:
        return [asdict(p) for p in self.parameters]
