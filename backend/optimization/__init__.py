"""
Optimization Engine for AI Academic Assistant
Provides metaheuristic optimization algorithms (GA, PSO, GWO, NSGA-II, Hybrid GA+PSO)
for optimizing the document retrieval pipeline under multi-objective constraints.
"""

from .search_space import SearchSpace, ParameterSpec
from .constraints import ConstraintHandler
from .fitness import FitnessEvaluator, FitnessWeights
from .evaluation import RetrievalEvaluator
from .base_optimizer import BaseOptimizer
from .baseline import BaselineOptimizer
from .ga import GeneticAlgorithmOptimizer
from .pso import ParticleSwarmOptimizer
from .gwo import GreyWolfOptimizer
from .nsga2 import NSGA2Optimizer
from .hybrid_ga_pso import HybridGAPSOOptimizer
from .active_config import get_active_config, set_active_config, RetrievalConfig

__all__ = [
    "SearchSpace",
    "ParameterSpec",
    "ConstraintHandler",
    "FitnessEvaluator",
    "FitnessWeights",
    "RetrievalEvaluator",
    "BaseOptimizer",
    "BaselineOptimizer",
    "GeneticAlgorithmOptimizer",
    "ParticleSwarmOptimizer",
    "GreyWolfOptimizer",
    "NSGA2Optimizer",
    "HybridGAPSOOptimizer",
    "get_active_config",
    "set_active_config",
    "RetrievalConfig",
]
