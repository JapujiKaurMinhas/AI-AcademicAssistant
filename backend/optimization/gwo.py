import time
import random
import numpy as np
from typing import List, Dict, Any
from .base_optimizer import BaseOptimizer, OptimizerResult, ConvergencePoint

class GreyWolfOptimizer(BaseOptimizer):
    """
    Real Grey Wolf Optimizer (GWO) based on Mirjalili et al. (2014).
    Social Hierarchy:
    - Alpha (α): First best candidate solution (dominant leader)
    - Beta (β): Second best candidate solution (advisor)
    - Delta (δ): Third best candidate solution (sentinel/elder)
    - Omega (ω): Subordinate wolves following α, β, δ
    
    Hunting & Encircling Equations:
        D_alpha = |C1 * X_alpha - X|
        X1 = X_alpha - A1 * D_alpha
        D_beta = |C2 * X_beta - X|
        X2 = X_beta - A2 * D_beta
        D_delta = |C3 * X_delta - X|
        X3 = X_delta - A3 * D_delta
        X(t+1) = (X1 + X2 + X3) / 3
    Where:
        a decreases linearly from 2 to 0: a = 2 * (1 - t / T)
        A = 2 * a * r1 - a   (|A| > 1 exploration, |A| < 1 exploitation)
        C = 2 * r2
    """
    def optimize(
        self,
        population_size: int = 15,
        iterations: int = 10,
        **kwargs
    ) -> OptimizerResult:
        start_time = time.perf_counter()
        dim = self.space.dimension

        # 1. Initialize Grey Wolf Pack
        pack: List[List[float]] = []
        # Seed first wolf with default baseline
        pack.append(self.constraints.repair(self.space.get_default_vector()))
        for _ in range(population_size - 1):
            pack.append(self.constraints.repair(self.space.sample_vector()))

        # Alpha, Beta, Delta vectors and fitnesses
        alpha_pos: List[float] = None
        alpha_score: float = -float("inf")
        alpha_metrics: Dict[str, Any] = None

        beta_pos: List[float] = None
        beta_score: float = -float("inf")

        delta_pos: List[float] = None
        delta_score: float = -float("inf")

        convergence_history: List[Dict[str, Any]] = []
        diversity_history: List[float] = []
        premature_convergence_flag = False

        # 2. Hunting Loop
        for it in range(1, iterations + 1):
            # Parameter 'a' linearly decreases from 2 to 0
            a = 2.0 * (1.0 - (it / max(1, iterations)))

            fitness_scores = []
            metrics_list = []

            # Evaluate Pack
            for wolf in pack:
                fit, met, pen = self.evaluate_vector(wolf)
                fitness_scores.append(fit)
                metrics_list.append(met)

                # Update Alpha, Beta, Delta hierarchy
                if fit > alpha_score:
                    delta_score = beta_score
                    delta_pos = list(beta_pos) if beta_pos else None

                    beta_score = alpha_score
                    beta_pos = list(alpha_pos) if alpha_pos else None

                    alpha_score = fit
                    alpha_pos = list(wolf)
                    alpha_metrics = dict(met)

                elif fit > beta_score and fit < alpha_score:
                    delta_score = beta_score
                    delta_pos = list(beta_pos) if beta_pos else None

                    beta_score = fit
                    beta_pos = list(wolf)

                elif fit > delta_score and fit < beta_score:
                    delta_score = fit
                    delta_pos = list(wolf)

            # Ensure Beta and Delta exist if pack has low initial variance
            if beta_pos is None:
                beta_pos = list(alpha_pos)
                beta_score = alpha_score
            if delta_pos is None:
                delta_pos = list(beta_pos)
                delta_score = beta_score

            # Compute Pack Diversity
            diversity = self.compute_population_diversity(pack)
            diversity_history.append(diversity)

            if self.check_premature_convergence(diversity, it, iterations):
                premature_convergence_flag = True

            mean_fitness = round(float(np.mean(fitness_scores)), 5)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            convergence_history.append(
                ConvergencePoint(
                    iteration=it,
                    best_fitness=alpha_score,
                    mean_fitness=mean_fitness,
                    diversity=diversity,
                    best_parameters=self.space.to_dict(alpha_pos),
                    exploration_rate=round(a / 2.0, 3), # Normalized exploration coefficient
                    elapsed_time_ms=round(elapsed_ms, 2)
                ).__dict__
            )

            # Check Termination
            if it == iterations:
                break

            # 3. Update Omega Wolf Positions based on Alpha, Beta, Delta
            new_pack = []
            for i in range(population_size):
                new_pos = []
                for d in range(dim):
                    # Alpha influence
                    r1 = random.random()
                    r2 = random.random()
                    A1 = 2.0 * a * r1 - a
                    C1 = 2.0 * r2
                    D_alpha = abs(C1 * alpha_pos[d] - pack[i][d])
                    X1 = alpha_pos[d] - A1 * D_alpha

                    # Beta influence
                    r1 = random.random()
                    r2 = random.random()
                    A2 = 2.0 * a * r1 - a
                    C2 = 2.0 * r2
                    D_beta = abs(C2 * beta_pos[d] - pack[i][d])
                    X2 = beta_pos[d] - A2 * D_beta

                    # Delta influence
                    r1 = random.random()
                    r2 = random.random()
                    A3 = 2.0 * a * r1 - a
                    C3 = 2.0 * r2
                    D_delta = abs(C3 * delta_pos[d] - pack[i][d])
                    X3 = delta_pos[d] - A3 * D_delta

                    # Average positions
                    X_new = (X1 + X2 + X3) / 3.0
                    new_pos.append(X_new)

                repaired_pos = self.constraints.repair(new_pos)
                new_pack.append(repaired_pos)

            pack = new_pack

        total_runtime = time.perf_counter() - start_time

        return OptimizerResult(
            algorithm="Grey Wolf Optimizer (GWO)",
            best_parameters=self.space.to_dict(alpha_pos),
            best_fitness=alpha_score,
            metrics=alpha_metrics,
            runtime_seconds=round(total_runtime, 4),
            convergence_history=convergence_history,
            diversity_history=diversity_history,
            premature_convergence_detected=premature_convergence_flag,
            iterations_run=iterations,
            population_size=population_size,
            random_seed=self.seed
        )
