import time
import random
import numpy as np
from typing import List, Dict, Any, Tuple
from .base_optimizer import BaseOptimizer, OptimizerResult, ConvergencePoint

class Individual:
    def __init__(self, vector: List[float]):
        self.vector = list(vector)
        self.objectives: List[float] = [] # [Obj1: -Quality, Obj2: Latency, Obj3: Tokens] (all minimized)
        self.metrics: Dict[str, Any] = {}
        self.rank: int = 0
        self.crowding_distance: float = 0.0
        self.dominated_solutions: List['Individual'] = []
        self.domination_count: int = 0


class NSGA2Optimizer(BaseOptimizer):
    """
    Real Non-dominated Sorting Genetic Algorithm II (NSGA-II) by Deb et al. (2002).
    Optimizes 3 simultaneous conflicting objectives for RAG document retrieval:
        Obj 1: MAXIMIZE Retrieval Quality (f1 = -Quality, minimized)
        Obj 2: MINIMIZE Retrieval Latency (f2 = Latency ms, minimized)
        Obj 3: MINIMIZE Token Cost (f3 = Tokens used, minimized)
    Features:
    - Fast non-dominated sorting into Pareto fronts F1, F2, ...
    - Crowding distance assignment to maintain solution spread along the trade-off surface
    - Crowded comparison operator for tournament selection
    - Elite (2N -> N) generation replacement
    - Extraction of non-dominated Pareto Front for user inspection and application
    """
    def optimize(
        self,
        population_size: int = 16,
        iterations: int = 10,
        crossover_prob: float = 0.85,
        mutation_prob: float = 0.20,
        **kwargs
    ) -> OptimizerResult:
        start_time = time.perf_counter()

        # 1. Population Initialization
        population: List[Individual] = []
        # Seed first with baseline
        first_vec = self.constraints.repair(self.space.get_default_vector())
        population.append(Individual(first_vec))

        for _ in range(population_size - 1):
            vec = self.constraints.repair(self.space.sample_vector())
            population.append(Individual(vec))

        # Initial evaluation
        for ind in population:
            self._evaluate_individual(ind)

        # Fast non-dominated sort
        fronts = self._fast_non_dominated_sort(population)
        for front in fronts:
            self._calculate_crowding_distance(front)

        convergence_history: List[Dict[str, Any]] = []
        diversity_history: List[float] = []
        premature_convergence_flag = False

        # 2. Evolutionary Loop
        for gen in range(1, iterations + 1):
            # Population diversity
            pop_vectors = [ind.vector for ind in population]
            diversity = self.compute_population_diversity(pop_vectors)
            diversity_history.append(diversity)

            if self.check_premature_convergence(diversity, gen, iterations):
                premature_convergence_flag = True

            # Get best quality solution from Front 1 for single-value tracking
            front1 = fronts[0] if fronts else population
            best_quality_ind = min(front1, key=lambda ind: ind.objectives[0]) # Recall obj0 is -Quality
            best_quality = -best_quality_ind.objectives[0]

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            convergence_history.append(
                ConvergencePoint(
                    iteration=gen,
                    best_fitness=round(best_quality, 4),
                    mean_fitness=round(float(np.mean([-ind.objectives[0] for ind in population])), 4),
                    diversity=diversity,
                    best_parameters=self.space.to_dict(best_quality_ind.vector),
                    exploration_rate=round(mutation_prob, 3),
                    elapsed_time_ms=round(elapsed_ms, 2)
                ).__dict__
            )

            # Check Termination
            if gen == iterations:
                break

            # 3. Offspring Generation (Selection, Crossover, Mutation)
            offspring: List[Individual] = []
            while len(offspring) < population_size:
                p1 = self._crowded_tournament_select(population)
                p2 = self._crowded_tournament_select(population)

                if random.random() < crossover_prob:
                    c1_vec, c2_vec = self._crossover(p1.vector, p2.vector)
                else:
                    c1_vec, c2_vec = list(p1.vector), list(p2.vector)

                c1_vec = self._mutate(c1_vec, mutation_prob)
                c1 = Individual(self.constraints.repair(c1_vec))
                self._evaluate_individual(c1)
                offspring.append(c1)

                if len(offspring) < population_size:
                    c2_vec = self._mutate(c2_vec, mutation_prob)
                    c2 = Individual(self.constraints.repair(c2_vec))
                    self._evaluate_individual(c2)
                    offspring.append(c2)

            # 4. Replacement: Combine Parent (N) and Offspring (N) -> Pool of 2N
            combined = population + offspring
            fronts = self._fast_non_dominated_sort(combined)

            new_population: List[Individual] = []
            for front in fronts:
                self._calculate_crowding_distance(front)
                if len(new_population) + len(front) <= population_size:
                    new_population.extend(front)
                else:
                    # Sort front by crowding distance descending and fill remainder
                    front.sort(key=lambda ind: ind.crowding_distance, reverse=True)
                    needed = population_size - len(new_population)
                    new_population.extend(front[:needed])
                    break

            population = new_population
            fronts = self._fast_non_dominated_sort(population)
            for front in fronts:
                self._calculate_crowding_distance(front)

        total_runtime = time.perf_counter() - start_time

        # Extract final Pareto Front (Rank 1 solutions)
        pareto_front_inds = fronts[0] if fronts else population
        pareto_front = []
        for ind in pareto_front_inds:
            quality = round(-ind.objectives[0], 4)
            latency = round(ind.objectives[1], 1)
            tokens = int(ind.objectives[2])
            pareto_front.append({
                "parameters": self.space.to_dict(ind.vector),
                "quality": quality,
                "latency_ms": latency,
                "tokens": tokens,
                "crowding_distance": round(ind.crowding_distance, 4),
                "metrics": ind.metrics
            })

        # Sort Pareto front by quality descending
        pareto_front.sort(key=lambda item: item["quality"], reverse=True)

        best_ind = pareto_front_inds[0]
        return OptimizerResult(
            algorithm="NSGA-II (Multi-Objective)",
            best_parameters=self.space.to_dict(best_ind.vector),
            best_fitness=round(-best_ind.objectives[0], 4),
            metrics=best_ind.metrics,
            runtime_seconds=round(total_runtime, 4),
            convergence_history=convergence_history,
            diversity_history=diversity_history,
            pareto_front=pareto_front,
            premature_convergence_detected=premature_convergence_flag,
            iterations_run=iterations,
            population_size=population_size,
            random_seed=self.seed
        )

    def _evaluate_individual(self, ind: Individual):
        repaired = self.constraints.repair(ind.vector)
        ind.vector = repaired
        p_dict = self.space.to_dict(repaired)

        metrics = self.evaluator.evaluate_candidate(
            chunk_size=p_dict["chunk_size"],
            chunk_overlap=p_dict["chunk_overlap"],
            top_k=p_dict["top_k"],
            similarity_threshold=p_dict["similarity_threshold"],
            context_token_budget=p_dict["context_token_budget"]
        )
        ind.metrics = metrics
        ind.objectives = self.fitness.evaluate_multi_objective(metrics)

    def _dominates(self, ind1: Individual, ind2: Individual) -> bool:
        """True if ind1 dominates ind2 (all objectives <= and at least one strictly <)."""
        not_worse = all(o1 <= o2 for o1, o2 in zip(ind1.objectives, ind2.objectives))
        strictly_better = any(o1 < o2 for o1, o2 in zip(ind1.objectives, ind2.objectives))
        return not_worse and strictly_better

    def _fast_non_dominated_sort(self, population: List[Individual]) -> List[List[Individual]]:
        fronts: List[List[Individual]] = [[]]
        for p in population:
            p.dominated_solutions = []
            p.domination_count = 0
            for q in population:
                if self._dominates(p, q):
                    p.dominated_solutions.append(q)
                elif self._dominates(q, p):
                    p.domination_count += 1
            if p.domination_count == 0:
                p.rank = 1
                fronts[0].append(p)

        i = 0
        while len(fronts[i]) > 0:
            next_front = []
            for p in fronts[i]:
                for q in p.dominated_solutions:
                    q.domination_count -= 1
                    if q.domination_count == 0:
                        q.rank = i + 2
                        next_front.append(q)
            i += 1
            fronts.append(next_front)

        if len(fronts[-1]) == 0:
            fronts.pop()
        return fronts

    def _calculate_crowding_distance(self, front: List[Individual]):
        l = len(front)
        if l == 0:
            return
        if l <= 2:
            for ind in front:
                ind.crowding_distance = float("inf")
            return

        for ind in front:
            ind.crowding_distance = 0.0

        num_objectives = len(front[0].objectives)
        for m in range(num_objectives):
            front.sort(key=lambda ind: ind.objectives[m])
            front[0].crowding_distance = float("inf")
            front[-1].crowding_distance = float("inf")

            obj_min = front[0].objectives[m]
            obj_max = front[-1].objectives[m]
            span = obj_max - obj_min
            if span == 0:
                continue

            for i in range(1, l - 1):
                if front[i].crowding_distance != float("inf"):
                    front[i].crowding_distance += (front[i + 1].objectives[m] - front[i - 1].objectives[m]) / span

    def _crowded_tournament_select(self, population: List[Individual]) -> Individual:
        i1, i2 = random.sample(population, 2)
        if i1.rank < i2.rank:
            return i1
        elif i2.rank < i1.rank:
            return i2
        elif i1.crowding_distance > i2.crowding_distance:
            return i1
        elif i2.crowding_distance > i1.crowding_distance:
            return i2
        return random.choice([i1, i2])

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
