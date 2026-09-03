import time
from typing import Dict, Any, List
from .search_space import SearchSpace
from .constraints import ConstraintHandler
from .evaluation import RetrievalEvaluator
from .fitness import FitnessEvaluator
from .ga import GeneticAlgorithmOptimizer

class AblationStudyRunner:
    """
    Executes a 5-configuration ablation study to isolate the empirical impact
    of optimizing individual parameter subsets versus full pipeline optimization.
    Configurations:
    A. Baseline: No optimization (all parameters at manual defaults)
    B. Stage 1: Optimize Chunk Size only (fixed overlap, top_k, threshold, budget)
    C. Stage 2: Optimize Chunk Size + Chunk Overlap
    D. Stage 3: Optimize Retrieval Parameters (Top-K + Similarity Threshold)
    E. Full System: Simultaneous optimization of all 5 parameters
    """
    def __init__(
        self,
        evaluator: RetrievalEvaluator,
        fitness_evaluator: FitnessEvaluator,
        iterations: int = 8,
        population_size: int = 10,
        random_seed: int = 42
    ):
        self.evaluator = evaluator
        self.fitness = fitness_evaluator
        self.iterations = iterations
        self.population_size = population_size
        self.seed = random_seed
        self.space = SearchSpace()

    def run_ablation(self) -> List[Dict[str, Any]]:
        results = []
        default = self.space.get_default_vector()

        # Config A: Baseline
        metrics_a = self.evaluator.evaluate_candidate(
            chunk_size=int(default[0]),
            chunk_overlap=int(default[1]),
            top_k=int(default[2]),
            similarity_threshold=default[3],
            context_token_budget=int(default[4])
        )
        fit_a = self.fitness.evaluate(metrics_a)
        results.append({
            "stage": "A",
            "name": "No Optimization (Baseline)",
            "description": "All parameters fixed to manual defaults",
            "optimized_parameters": ["None"],
            "parameters": self.space.to_dict(default),
            "fitness": fit_a,
            "quality": metrics_a["retrieval_quality"],
            "latency_ms": metrics_a["latency_ms"],
            "tokens": metrics_a["estimated_tokens"]
        })

        # Config B: Chunk size only
        bounds_b = {
            "chunk_overlap": (default[1], default[1]),
            "top_k": (default[2], default[2]),
            "similarity_threshold": (default[3], default[3]),
            "context_token_budget": (default[4], default[4])
        }
        space_b = SearchSpace(bounds_b)
        ga_b = GeneticAlgorithmOptimizer(space_b, ConstraintHandler(space_b), self.evaluator, self.fitness, self.seed)
        res_b = ga_b.optimize(population_size=self.population_size, iterations=self.iterations)
        results.append({
            "stage": "B",
            "name": "Optimize Chunk Size Only",
            "description": "Explores optimal chunk granularity while holding overlap and retrieval fixed",
            "optimized_parameters": ["chunk_size"],
            "parameters": res_b.best_parameters,
            "fitness": res_b.best_fitness,
            "quality": res_b.metrics["retrieval_quality"],
            "latency_ms": res_b.metrics["latency_ms"],
            "tokens": res_b.metrics["estimated_tokens"]
        })

        # Config C: Chunk size + Overlap
        bounds_c = {
            "top_k": (default[2], default[2]),
            "similarity_threshold": (default[3], default[3]),
            "context_token_budget": (default[4], default[4])
        }
        space_c = SearchSpace(bounds_c)
        ga_c = GeneticAlgorithmOptimizer(space_c, ConstraintHandler(space_c), self.evaluator, self.fitness, self.seed)
        res_c = ga_c.optimize(population_size=self.population_size, iterations=self.iterations)
        results.append({
            "stage": "C",
            "name": "Optimize Chunk Size + Overlap",
            "description": "Jointly optimizes segmentation size and boundary overlap",
            "optimized_parameters": ["chunk_size", "chunk_overlap"],
            "parameters": res_c.best_parameters,
            "fitness": res_c.best_fitness,
            "quality": res_c.metrics["retrieval_quality"],
            "latency_ms": res_c.metrics["latency_ms"],
            "tokens": res_c.metrics["estimated_tokens"]
        })

        # Config D: Top-K + Similarity Threshold
        bounds_d = {
            "chunk_size": (default[0], default[0]),
            "chunk_overlap": (default[1], default[1]),
            "context_token_budget": (default[4], default[4])
        }
        space_d = SearchSpace(bounds_d)
        ga_d = GeneticAlgorithmOptimizer(space_d, ConstraintHandler(space_d), self.evaluator, self.fitness, self.seed)
        res_d = ga_d.optimize(population_size=self.population_size, iterations=self.iterations)
        results.append({
            "stage": "D",
            "name": "Optimize Retrieval (Top-K + Threshold)",
            "description": "Optimizes ranking count and similarity filter with fixed document chunking",
            "optimized_parameters": ["top_k", "similarity_threshold"],
            "parameters": res_d.best_parameters,
            "fitness": res_d.best_fitness,
            "quality": res_d.metrics["retrieval_quality"],
            "latency_ms": res_d.metrics["latency_ms"],
            "tokens": res_d.metrics["estimated_tokens"]
        })

        # Config E: Full Optimization (All 5 parameters)
        space_e = SearchSpace()
        ga_e = GeneticAlgorithmOptimizer(space_e, ConstraintHandler(space_e), self.evaluator, self.fitness, self.seed)
        res_e = ga_e.optimize(population_size=self.population_size, iterations=self.iterations)
        results.append({
            "stage": "E",
            "name": "Full Multi-Parameter Optimization",
            "description": "Full end-to-end co-optimization of all 5 retrieval and context parameters",
            "optimized_parameters": ["chunk_size", "chunk_overlap", "top_k", "similarity_threshold", "context_token_budget"],
            "parameters": res_e.best_parameters,
            "fitness": res_e.best_fitness,
            "quality": res_e.metrics["retrieval_quality"],
            "latency_ms": res_e.metrics["latency_ms"],
            "tokens": res_e.metrics["estimated_tokens"]
        })

        return results
