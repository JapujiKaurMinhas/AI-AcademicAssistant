import random
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from .search_space import SearchSpace
from .constraints import ConstraintHandler
from .evaluation import RetrievalEvaluator
from .fitness import FitnessEvaluator

@dataclass
class ConvergencePoint:
    iteration: int
    best_fitness: float
    mean_fitness: float
    diversity: float
    best_parameters: Dict[str, Any]
    exploration_rate: float = 0.0
    elapsed_time_ms: float = 0.0

@dataclass
class OptimizerResult:
    algorithm: str
    best_parameters: Dict[str, Any]
    best_fitness: float
    metrics: Dict[str, Any]
    runtime_seconds: float
    convergence_history: List[Dict[str, Any]] = field(default_factory=list)
    diversity_history: List[float] = field(default_factory=list)
    pareto_front: Optional[List[Dict[str, Any]]] = None
    premature_convergence_detected: bool = False
    iterations_run: int = 0
    population_size: int = 0
    random_seed: int = 42

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseOptimizer(ABC):
    """
    Abstract Base Class for all metaheuristic and baseline retrieval optimizers.
    Ensures consistent convergence logging, diversity tracking, and state serialization.
    """
    def __init__(
        self,
        search_space: SearchSpace,
        constraint_handler: ConstraintHandler,
        evaluator: RetrievalEvaluator,
        fitness_evaluator: FitnessEvaluator,
        random_seed: int = 42
    ):
        self.space = search_space
        self.constraints = constraint_handler
        self.evaluator = evaluator
        self.fitness = fitness_evaluator
        self.seed = random_seed
        self.set_seed(random_seed)

    def set_seed(self, seed: int):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)

    def evaluate_vector(self, vec: List[float]) -> Tuple[float, Dict[str, Any], float]:
        """
        Repairs vector, evaluates real retrieval metrics, and returns (fitness, metrics, penalty).
        """
        repaired_vec = self.constraints.repair(vec)
        p_dict = self.space.to_dict(repaired_vec)
        
        metrics = self.evaluator.evaluate_candidate(
            chunk_size=p_dict["chunk_size"],
            chunk_overlap=p_dict["chunk_overlap"],
            top_k=p_dict["top_k"],
            similarity_threshold=p_dict["similarity_threshold"],
            context_token_budget=p_dict["context_token_budget"]
        )
        
        penalty = self.constraints.compute_penalty(repaired_vec, metrics)
        fitness_val = self.fitness.evaluate(metrics, penalty)
        
        return fitness_val, metrics, penalty

    def compute_population_diversity(self, population: List[List[float]]) -> float:
        """
        Calculates population diversity as the mean pairwise Euclidean distance
        in the normalized [0, 1]^D parameter space.
        """
        if len(population) < 2:
            return 0.0

        norm_pop = [np.array(self.space.normalize_vector(v)) for v in population]
        n = len(norm_pop)
        distances = []
        
        for i in range(n):
            for j in range(i + 1, n):
                d = np.linalg.norm(norm_pop[i] - norm_pop[j])
                distances.append(d)
                
        # Maximum distance in D-dimensional unit hypercube is sqrt(D)
        max_dist = np.sqrt(self.space.dimension)
        mean_dist = float(np.mean(distances)) if distances else 0.0
        normalized_diversity = round(mean_dist / max_dist, 4)
        return normalized_diversity

    def check_premature_convergence(
        self,
        diversity: float,
        iteration: int,
        total_iterations: int,
        threshold: float = 0.05
    ) -> bool:
        """
        Flags premature convergence if population diversity drops below threshold
        before 50% of the optimization budget has been consumed.
        """
        if total_iterations <= 1:
            return False
        return (iteration < 0.5 * total_iterations) and (diversity < threshold)

    @abstractmethod
    def optimize(self, population_size: int, iterations: int, **kwargs) -> OptimizerResult:
        """Execute the optimization search."""
        pass
