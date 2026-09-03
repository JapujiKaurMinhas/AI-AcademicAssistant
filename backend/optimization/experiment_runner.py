import time
import numpy as np
from typing import Dict, Any, List, Type
from .search_space import SearchSpace
from .constraints import ConstraintHandler
from .evaluation import RetrievalEvaluator
from .fitness import FitnessEvaluator, FitnessWeights
from .base_optimizer import BaseOptimizer, OptimizerResult
from .baseline import BaselineOptimizer
from .ga import GeneticAlgorithmOptimizer
from .pso import ParticleSwarmOptimizer
from .gwo import GreyWolfOptimizer
from .nsga2 import NSGA2Optimizer
from .hybrid_ga_pso import HybridGAPSOOptimizer

ALGORITHM_MAP = {
    "baseline": BaselineOptimizer,
    "ga": GeneticAlgorithmOptimizer,
    "pso": ParticleSwarmOptimizer,
    "gwo": GreyWolfOptimizer,
    "nsga2": NSGA2Optimizer,
    "hybrid": HybridGAPSOOptimizer
}

class ExperimentRunner:
    """
    Executes single and multi-run stochastic experiments across metaheuristic algorithms.
    Computes statistical summaries (mean, std, min, max) across runs for scientific rigor.
    """
    def __init__(
        self,
        evaluator: RetrievalEvaluator,
        weights: FitnessWeights = None,
        custom_bounds: Dict[str, Any] = None
    ):
        self.evaluator = evaluator
        self.space = SearchSpace(custom_bounds)
        self.constraints = ConstraintHandler(self.space)
        self.fitness = FitnessEvaluator(weights or FitnessWeights())

    def run_single(
        self,
        algorithm_name: str,
        population_size: int = 15,
        iterations: int = 10,
        random_seed: int = 42,
        **algo_kwargs
    ) -> OptimizerResult:
        algo_key = algorithm_name.lower().replace("-", "").replace("_", "").replace(" ", "")
        matched_key = None
        for k in ALGORITHM_MAP:
            if k in algo_key:
                matched_key = k
                break
        if not matched_key:
            matched_key = "ga"

        cls = ALGORITHM_MAP[matched_key]
        optimizer: BaseOptimizer = cls(
            search_space=self.space,
            constraint_handler=self.constraints,
            evaluator=self.evaluator,
            fitness_evaluator=self.fitness,
            random_seed=random_seed
        )

        return optimizer.optimize(
            population_size=population_size,
            iterations=iterations,
            **algo_kwargs
        )

    def run_multi_statistical(
        self,
        algorithm_name: str,
        num_runs: int = 3,
        population_size: int = 12,
        iterations: int = 8,
        base_seed: int = 42,
        **algo_kwargs
    ) -> Dict[str, Any]:
        """
        Executes N repeated runs with distinct seeds and calculates standard statistical metrics.
        """
        runs_results: List[OptimizerResult] = []
        for run_idx in range(num_runs):
            seed = base_seed + run_idx * 17
            res = self.run_single(
                algorithm_name=algorithm_name,
                population_size=population_size,
                iterations=iterations,
                random_seed=seed,
                **algo_kwargs
            )
            runs_results.append(res)

        fitnesses = [r.best_fitness for r in runs_results]
        qualities = [r.metrics["retrieval_quality"] for r in runs_results]
        latencies = [r.metrics["latency_ms"] for r in runs_results]
        tokens = [r.metrics["estimated_tokens"] for r in runs_results]
        runtimes = [r.runtime_seconds for r in runs_results]

        best_run_idx = int(np.argmax(fitnesses))
        best_overall_result = runs_results[best_run_idx]

        stats = {
            "num_runs": num_runs,
            "algorithm": runs_results[0].algorithm,
            "fitness": {
                "mean": round(float(np.mean(fitnesses)), 5),
                "std": round(float(np.std(fitnesses)), 5),
                "min": round(float(np.min(fitnesses)), 5),
                "max": round(float(np.max(fitnesses)), 5)
            },
            "retrieval_quality": {
                "mean": round(float(np.mean(qualities)), 4),
                "std": round(float(np.std(qualities)), 4),
                "min": round(float(np.min(qualities)), 4),
                "max": round(float(np.max(qualities)), 4)
            },
            "latency_ms": {
                "mean": round(float(np.mean(latencies)), 2),
                "std": round(float(np.std(latencies)), 2),
                "min": round(float(np.min(latencies)), 2),
                "max": round(float(np.max(latencies)), 2)
            },
            "tokens": {
                "mean": int(np.mean(tokens)),
                "std": round(float(np.std(tokens)), 1),
                "min": int(np.min(tokens)),
                "max": int(np.max(tokens))
            },
            "runtime_seconds": {
                "mean": round(float(np.mean(runtimes)), 3),
                "total": round(float(np.sum(runtimes)), 3)
            },
            "runs": [
                {
                    "run": i + 1,
                    "seed": r.random_seed,
                    "fitness": r.best_fitness,
                    "quality": r.metrics["retrieval_quality"],
                    "latency_ms": r.metrics["latency_ms"],
                    "tokens": r.metrics["estimated_tokens"],
                    "best_parameters": r.best_parameters
                }
                for i, r in enumerate(runs_results)
            ],
            "best_run": best_overall_result.to_dict()
        }
        return stats

    def run_algorithm_comparison(
        self,
        population_size: int = 12,
        iterations: int = 8,
        random_seed: int = 42
    ) -> List[Dict[str, Any]]:
        """
        Executes a direct comparative benchmark across all 6 algorithms under identical conditions.
        """
        comparison_results = []
        algorithms = [
            ("Baseline (Manual Default)", "baseline"),
            ("Genetic Algorithm (GA)", "ga"),
            ("Particle Swarm Optimization (PSO)", "pso"),
            ("Grey Wolf Optimizer (GWO)", "gwo"),
            ("NSGA-II (Multi-Objective)", "nsga2"),
            ("Hybrid GA + PSO", "hybrid")
        ]

        for label, key in algorithms:
            res = self.run_single(
                algorithm_name=key,
                population_size=population_size,
                iterations=iterations,
                random_seed=random_seed
            )
            comparison_results.append({
                "algorithm": res.algorithm,
                "best_fitness": res.best_fitness,
                "retrieval_quality": res.metrics["retrieval_quality"],
                "semantic_similarity": res.metrics["semantic_similarity"],
                "context_coverage": res.metrics["context_coverage"],
                "latency_ms": res.metrics["latency_ms"],
                "estimated_tokens": res.metrics["estimated_tokens"],
                "runtime_seconds": res.runtime_seconds,
                "best_parameters": res.best_parameters,
                "convergence_history": res.convergence_history
            })

        return comparison_results
