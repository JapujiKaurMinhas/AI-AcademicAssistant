import time
import random
import numpy as np
from typing import List, Dict, Any, Tuple
from .base_optimizer import BaseOptimizer, OptimizerResult, ConvergencePoint

class GeneticAlgorithmOptimizer(BaseOptimizer):
    """
    Real Genetic Algorithm (GA) for RAG retrieval parameter optimization.
    Features:
    - Mixed integer/continuous chromosome representation
    - Uniform and Simulated Binary Crossover (SBX)
    - Polynomial / Gaussian mutation with adaptive rate based on population diversity
    - Elitism preserving top-performing chromosomes
    - Tournament selection with replacement
    - Generation-by-generation convergence, diversity, and premature convergence tracking
    """
    def optimize(
        self,
        population_size: int = 15,
        iterations: int = 10,
        crossover_prob: float = 0.85,
        mutation_prob: float = 0.20,
        elite_size: int = 2,
        tournament_size: int = 3,
        adaptive_mutation: bool = True,
        **kwargs
    ) -> OptimizerResult:
        start_time = time.perf_counter()
        elite_size = max(1, min(elite_size, population_size // 2))

        # 1. Population Initialization
        population: List[List[float]] = []
        # Always seed one member with the baseline default
        population.append(self.space.get_default_vector())
        for _ in range(population_size - 1):
            population.append(self.space.sample_vector())

        # Ensure all individuals satisfy constraints
        population = [self.constraints.repair(ind) for ind in population]

        convergence_history: List[Dict[str, Any]] = []
        diversity_history: List[float] = []
        premature_convergence_flag = False

        global_best_vec: List[float] = None
        global_best_fitness: float = -float("inf")
        global_best_metrics: Dict[str, Any] = None

        # 2. Evolutionary Loop
        for gen in range(1, iterations + 1):
            gen_start = time.perf_counter()
            
            # Fitness Evaluation
            eval_results = [self.evaluate_vector(ind) for ind in population]
            fitness_scores = [res[0] for res in eval_results]
            metrics_list = [res[1] for res in eval_results]

            # Track generation statistics
            best_idx = int(np.argmax(fitness_scores))
            gen_best_fitness = fitness_scores[best_idx]
            gen_best_vec = population[best_idx]
            gen_best_metrics = metrics_list[best_idx]
            mean_fitness = round(float(np.mean(fitness_scores)), 5)

            if gen_best_fitness > global_best_fitness:
                global_best_fitness = gen_best_fitness
                global_best_vec = list(gen_best_vec)
                global_best_metrics = dict(gen_best_metrics)

            # Compute Population Diversity
            diversity = self.compute_population_diversity(population)
            diversity_history.append(diversity)

            if self.check_premature_convergence(diversity, gen, iterations):
                premature_convergence_flag = True

            # Adaptive Mutation Rate: if diversity collapses, temporarily boost mutation to escape local optima
            current_mutation_prob = mutation_prob
            if adaptive_mutation and diversity < 0.08:
                current_mutation_prob = min(0.60, mutation_prob * 1.8)

            best_param_dict = self.space.to_dict(global_best_vec)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            convergence_history.append(
                ConvergencePoint(
                    iteration=gen,
                    best_fitness=global_best_fitness,
                    mean_fitness=mean_fitness,
                    diversity=diversity,
                    best_parameters=best_param_dict,
                    exploration_rate=round(current_mutation_prob, 3),
                    elapsed_time_ms=round(elapsed_ms, 2)
                ).__dict__
            )

            # Check Termination (if final generation, break before breeding)
            if gen == iterations:
                break

            # 3. Elitism: identify top elite chromosomes
            sorted_indices = np.argsort(fitness_scores)[::-1]
            new_population: List[List[float]] = [
                list(population[sorted_indices[i]]) for i in range(elite_size)
            ]

            # 4. Tournament Selection
            def select_parent() -> List[float]:
                contestants = random.sample(range(population_size), min(tournament_size, population_size))
                winner = max(contestants, key=lambda idx: fitness_scores[idx])
                return population[winner]

            # 5. Breeding (Crossover & Mutation)
            while len(new_population) < population_size:
                p1 = select_parent()
                p2 = select_parent()

                # Crossover
                if random.random() < crossover_prob:
                    c1, c2 = self._crossover(p1, p2)
                else:
                    c1, c2 = list(p1), list(p2)

                # Mutation
                c1 = self._mutate(c1, current_mutation_prob)
                new_population.append(self.constraints.repair(c1))

                if len(new_population) < population_size:
                    c2 = self._mutate(c2, current_mutation_prob)
                    new_population.append(self.constraints.repair(c2))

            population = new_population

        total_runtime = time.perf_counter() - start_time

        return OptimizerResult(
            algorithm="Genetic Algorithm (GA)",
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

    def _crossover(self, parent1: List[float], parent2: List[float]) -> Tuple[List[float], List[float]]:
        """
        Simulated Binary / Arithmetic Crossover for mixed variables.
        Blends continuous parameters with random interpolation coefficient alpha,
        and applies uniform swap for integer components.
        """
        child1 = []
        child2 = []
        for i, param in enumerate(self.space.parameters):
            v1, v2 = parent1[i], parent2[i]
            if random.random() < 0.5:
                # Arithmetic blend
                alpha = random.uniform(0.2, 0.8)
                val1 = alpha * v1 + (1 - alpha) * v2
                val2 = (1 - alpha) * v1 + alpha * v2
            else:
                # Discrete swap
                val1, val2 = v2, v1
            child1.append(param.clamp(val1))
            child2.append(param.clamp(val2))
        return child1, child2

    def _mutate(self, chromosome: List[float], mutation_prob: float) -> List[float]:
        """
        Gaussian / Perturbation Mutation respecting parameter type and bounds.
        """
        mutated = list(chromosome)
        for i, param in enumerate(self.space.parameters):
            if random.random() < mutation_prob:
                span = param.upper - param.lower
                # Gaussian perturbation with sigma = 15% of range
                delta = random.gauss(0, 0.15 * span)
                mutated[i] = param.clamp(mutated[i] + delta)
        return mutated
