import time
import random
import numpy as np
from typing import List, Dict, Any, Tuple
from .base_optimizer import BaseOptimizer, OptimizerResult, ConvergencePoint
from .pso import Particle

class HybridGAPSOOptimizer(BaseOptimizer):
    """
    Hybrid GA + PSO Metaheuristic Optimizer.
    Rationale:
    - Genetic Algorithms excel at broad global exploration across diverse regions of the
      search space via crossover and mutation, preventing early stagnation.
    - Particle Swarm Optimization excels at rapid local exploitation and continuous refinement
      around promising candidate basins through velocity vector tracking.
    Execution Architecture:
    - Phase 1 (Generations 1 to G_ga): GA executes global exploration across the search space.
    - Phase 2 (Transition): Top candidate chromosomes from the final GA generation seed the PSO swarm.
    - Phase 3 (Iterations G_ga+1 to Total): PSO refines the promising candidates towards fine-grained local optima.
    """
    def optimize(
        self,
        population_size: int = 15,
        iterations: int = 12,
        ga_ratio: float = 0.50, # 50% iterations in GA phase, 50% in PSO phase
        crossover_prob: float = 0.85,
        mutation_prob: float = 0.20,
        elite_size: int = 2,
        cognitive_coeff: float = 1.7,
        social_coeff: float = 1.7,
        **kwargs
    ) -> OptimizerResult:
        start_time = time.perf_counter()
        dim = self.space.dimension
        v_max = [0.20 * (p.upper - p.lower) for p in self.space.parameters]

        ga_iterations = max(2, int(iterations * ga_ratio))
        pso_iterations = iterations - ga_iterations

        convergence_history: List[Dict[str, Any]] = []
        diversity_history: List[float] = []
        premature_convergence_flag = False

        global_best_vec: List[float] = None
        global_best_fitness: float = -float("inf")
        global_best_metrics: Dict[str, Any] = None

        # =========================================================================
        # PHASE 1: GA Global Exploration
        # =========================================================================
        ga_pop: List[List[float]] = []
        ga_pop.append(self.constraints.repair(self.space.get_default_vector()))
        for _ in range(population_size - 1):
            ga_pop.append(self.constraints.repair(self.space.sample_vector()))

        for gen in range(1, ga_iterations + 1):
            eval_results = [self.evaluate_vector(ind) for ind in ga_pop]
            fitness_scores = [r[0] for r in eval_results]
            metrics_list = [r[1] for r in eval_results]

            best_idx = int(np.argmax(fitness_scores))
            if fitness_scores[best_idx] > global_best_fitness:
                global_best_fitness = fitness_scores[best_idx]
                global_best_vec = list(ga_pop[best_idx])
                global_best_metrics = dict(metrics_list[best_idx])

            diversity = self.compute_population_diversity(ga_pop)
            diversity_history.append(diversity)

            if self.check_premature_convergence(diversity, gen, iterations):
                premature_convergence_flag = True

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            convergence_history.append(
                ConvergencePoint(
                    iteration=gen,
                    best_fitness=global_best_fitness,
                    mean_fitness=round(float(np.mean(fitness_scores)), 5),
                    diversity=diversity,
                    best_parameters=self.space.to_dict(global_best_vec),
                    exploration_rate=round(mutation_prob, 3),
                    elapsed_time_ms=round(elapsed_ms, 2)
                ).__dict__
            )

            # Breed next GA generation (except on last GA iteration)
            if gen < ga_iterations:
                sorted_indices = np.argsort(fitness_scores)[::-1]
                new_pop = [list(ga_pop[sorted_indices[i]]) for i in range(elite_size)]
                
                def select_parent():
                    contestants = random.sample(range(population_size), min(3, population_size))
                    winner = max(contestants, key=lambda idx: fitness_scores[idx])
                    return ga_pop[winner]

                while len(new_pop) < population_size:
                    p1 = select_parent()
                    p2 = select_parent()
                    c1, c2 = self._crossover(p1, p2)
                    new_pop.append(self.constraints.repair(self._mutate(c1, mutation_prob)))
                    if len(new_pop) < population_size:
                        new_pop.append(self.constraints.repair(self._mutate(c2, mutation_prob)))
                ga_pop = new_pop

        # =========================================================================
        # PHASE 2: Transition - Seed PSO Swarm from Best GA Candidates
        # =========================================================================
        sorted_indices = np.argsort(fitness_scores)[::-1]
        pso_swarm: List[Particle] = []
        for idx in sorted_indices[:population_size]:
            pos = list(ga_pop[idx])
            vel = [random.uniform(-0.5 * vm, 0.5 * vm) for vm in v_max]
            p = Particle(pos, vel)
            p.pbest_position = list(pos)
            p.pbest_fitness = fitness_scores[idx]
            p.pbest_metrics = dict(metrics_list[idx])
            pso_swarm.append(p)

        gbest_position = list(global_best_vec)
        gbest_fitness = global_best_fitness

        # =========================================================================
        # PHASE 3: PSO Local Refinement & Exploitation
        # =========================================================================
        for pso_step in range(1, pso_iterations + 1):
            current_iter = ga_iterations + pso_step
            # Linearly decaying inertia weight
            w = 0.80 - 0.40 * (pso_step / max(1, pso_iterations))

            fitness_scores = []
            positions = [p.position for p in pso_swarm]

            for p in pso_swarm:
                fit, met, pen = self.evaluate_vector(p.position)
                fitness_scores.append(fit)

                if fit > p.pbest_fitness:
                    p.pbest_fitness = fit
                    p.pbest_position = list(p.position)
                    p.pbest_metrics = dict(met)

                if fit > gbest_fitness:
                    gbest_fitness = fit
                    gbest_position = list(p.position)
                    global_best_vec = list(p.position)
                    global_best_fitness = fit
                    global_best_metrics = dict(met)

            diversity = self.compute_population_diversity(positions)
            diversity_history.append(diversity)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            convergence_history.append(
                ConvergencePoint(
                    iteration=current_iter,
                    best_fitness=gbest_fitness,
                    mean_fitness=round(float(np.mean(fitness_scores)), 5),
                    diversity=diversity,
                    best_parameters=self.space.to_dict(gbest_position),
                    exploration_rate=round(w, 3),
                    elapsed_time_ms=round(elapsed_ms, 2)
                ).__dict__
            )

            # Update Velocities & Positions
            if pso_step < pso_iterations:
                for p in pso_swarm:
                    for d in range(dim):
                        r1 = random.random()
                        r2 = random.random()
                        cog = cognitive_coeff * r1 * (p.pbest_position[d] - p.position[d])
                        soc = social_coeff * r2 * (gbest_position[d] - p.position[d])
                        new_vel = w * p.velocity[d] + cog + soc
                        new_vel = max(-v_max[d], min(v_max[d], new_vel))
                        p.velocity[d] = new_vel
                        p.position[d] += new_vel
                    p.position = self.constraints.repair(p.position)

        total_runtime = time.perf_counter() - start_time

        return OptimizerResult(
            algorithm="Hybrid GA + PSO",
            best_parameters=self.space.to_dict(global_best_vec),
            best_fitness=global_best_fitness,
            metrics=global_best_metrics,
            runtime_seconds=round(total_runtime, 4),
            convergence_history=convergence_history,
            diversity_history=diversity_history,
            premature_convergence_detected=premature_convergence_flag,
            iterations_run=iterations,
            population_size=population_size,
            random_seed=self.seed
        )

    def _crossover(self, p1: List[float], p2: List[float]) -> Tuple[List[float], List[float]]:
        c1, c2 = [], []
        for i, param in enumerate(self.space.parameters):
            if random.random() < 0.5:
                alpha = random.uniform(0.2, 0.8)
                c1.append(param.clamp(alpha * p1[i] + (1 - alpha) * p2[i]))
                c2.append(param.clamp((1 - alpha) * p1[i] + alpha * p2[i]))
            else:
                c1.append(p2[i])
                c2.append(p1[i])
        return c1, c2

    def _mutate(self, vec: List[float], mutation_prob: float) -> List[float]:
        mutated = list(vec)
        for i, param in enumerate(self.space.parameters):
            if random.random() < mutation_prob:
                span = param.upper - param.lower
                delta = random.gauss(0, 0.15 * span)
                mutated[i] = param.clamp(mutated[i] + delta)
        return mutated
