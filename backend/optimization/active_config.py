from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

@dataclass
class RetrievalConfig:
    chunk_size: int = 800
    chunk_overlap: int = 100
    top_k: int = 3
    similarity_threshold: float = 0.20
    context_token_budget: int = 3000
    mode: str = "default"  # "default" or "optimized"
    algorithm_source: Optional[str] = "Manual Default"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# Global in-memory configuration state
_active_config = RetrievalConfig()

def get_active_config() -> RetrievalConfig:
    global _active_config
    return _active_config

def set_active_config(
    chunk_size: int,
    chunk_overlap: int,
    top_k: int,
    similarity_threshold: float,
    context_token_budget: int,
    mode: str = "optimized",
    algorithm_source: str = "Optimized Configuration"
) -> RetrievalConfig:
    global _active_config
    _active_config = RetrievalConfig(
        chunk_size=int(chunk_size),
        chunk_overlap=int(chunk_overlap),
        top_k=int(top_k),
        similarity_threshold=round(float(similarity_threshold), 4),
        context_token_budget=int(context_token_budget),
        mode=mode,
        algorithm_source=algorithm_source
    )
    return _active_config

def reset_to_default() -> RetrievalConfig:
    global _active_config
    _active_config = RetrievalConfig(
        chunk_size=800,
        chunk_overlap=100,
        top_k=3,
        similarity_threshold=0.20,
        context_token_budget=3000,
        mode="default",
        algorithm_source="Manual Default"
    )
    return _active_config
