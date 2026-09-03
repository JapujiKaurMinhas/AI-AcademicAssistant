import time
from typing import Dict, Any
from .base_optimizer import BaseOptimizer, OptimizerResult, ConvergencePoint

class BaselineOptimizer(BaseOptimizer):
    """
    Evaluates the unoptimized baseline retrieval configuration representing
    standard default/manual parameters in the AI Academic Assistant.
    Provides a rigorous experimental control for metaheuristic comparisons.
    """
    def optimize(self, population_size: int = 1, iterations: int = 1, **kwargs) -> OptimizerResult:
        start_time = time.perf_counter()
        
        # Manually selected default baseline vector
        baseline_vec = self.space.get_default_vector()
        fitness_val, metrics, penalty = self.evaluate_vector(baseline_vec)
        
        runtime = time.perf_counter() - start_time
        param_dict = self.space.to_dict(baseline_vec)
        
        convergence_history = [
            ConvergencePoint(
                iteration=1,
                best_fitness=fitness_val,
                mean_fitness=fitness_val,
                diversity=0.0,
                best_parameters=param_dict,
                exploration_rate=0.0,
                elapsed_time_ms=round(runtime * 1000.0, 2)
            ).__dict__
        ]

        return OptimizerResult(
            algorithm="Baseline (Manual Default)",
            best_parameters=param_dict,
            best_fitness=fitness_val,
            metrics=metrics,
            runtime_seconds=round(runtime, 4),
            convergence_history=convergence_history,
            diversity_history=[0.0],
            premature_convergence_detected=False,
            iterations_run=1,
            population_size=1,
            random_seed=self.seed
        )
