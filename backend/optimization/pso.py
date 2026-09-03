import time
import random
import numpy as np
from typing import List, Dict, Any
from .base_optimizer import BaseOptimizer, OptimizerResult, ConvergencePoint

class Particle:
    def __init__(self, position: List[float], velocity: List[float]):
        self.position = list(position)
        self.velocity = list(velocity)
        self.pbest_position = list(position)
        self.pbest_fitness = -float("inf")
        self.pbest_metrics: Dict[str, Any] = {}
        self.current_fitness = -float("inf")
        self.current_metrics: Dict[str, Any] = {}


class ParticleSwarmOptimizer(BaseOptimizer):
    """
    Real Particle Swarm Optimization (PSO) for continuous & integer parameter spaces.
    Velocity Update Equation:
        v_{i}^{d}(t+1) = w(t) * v_{i}^{d}(t)
                       + c_1 * r_1 * (pBest_{i}^{d} - x_{i}^{d}(t))
                       + c_2 * r_2 * (gBest^{d} - x_{i}^{d}(t))
    Position Update Equation:
        x_{i}^{d}(t+1) = x_{i}^{d}(t) + v_{i}^{d}(t+1)
    Features:
    - Time-varying adaptive inertia weight w(t)
    - Cognitive (c1) and Social (c2) acceleration coefficients
    - Velocity clamping to prevent explosive particle dispersion
    - Particle swarm spread / diversity tracking
    """
    def optimize(
        self,
        population_size: int = 15,
        iterations: int = 10,
        inertia_weight_max: float = 0.90,
        inertia_weight_min: float = 0.40,
        cognitive_coeff: float = 1.70,
        social_coeff: float = 1.70,
        adaptive_inertia: bool = True,
        **kwargs
    ) -> OptimizerResult:
        start_time = time.perf_counter()
        dim = self.space.dimension

        # Define maximum velocity per dimension (typically 20% of the parameter span)
        v_max = [0.20 * (p.upper - p.lower) for p in self.parameters_spec]

        # 1. Swarm Initialization
        swarm: List[Particle] = []
        
        # Seed first particle with default baseline
        first_pos = self.constraints.repair(self.space.get_default_vector())
        first_vel = [0.0] * dim
        swarm.append(Particle(first_pos, first_vel))

        for _ in range(population_size - 1):
            pos = self.constraints.repair(self.space.sample_vector())
            vel = [random.uniform(-vm, vm) for vm in v_max]
            swarm.append(Particle(pos, vel))

        gbest_position: List[float] = None
        gbest_fitness: float = -float("inf")
        gbest_metrics: Dict[str, Any] = None

        convergence_history: List[Dict[str, Any]] = []
        diversity_history: List[float] = []
        premature_convergence_flag = False

        # 2. Iteration Loop
        for it in range(1, iterations + 1):
            # Compute adaptive inertia weight: w(t) decreases linearly from w_max to w_min
            if adaptive_inertia and iterations > 1:
                w = inertia_weight_max - (inertia_weight_max - inertia_weight_min) * (it / iterations)
            else:
                w = inertia_weight_max

            fitness_scores = []
            positions = [p.position for p in swarm]

            # Evaluate Swarm
            for particle in swarm:
                fit, met, pen = self.evaluate_vector(particle.position)
                particle.current_fitness = fit
                particle.current_metrics = met
                fitness_scores.append(fit)

                # Update Personal Best (pBest)
                if fit > particle.pbest_fitness:
                    particle.pbest_fitness = fit
                    particle.pbest_position = list(particle.position)
                    particle.pbest_metrics = dict(met)

                # Update Global Best (gBest)
                if fit > gbest_fitness:
                    gbest_fitness = fit
                    gbest_position = list(particle.position)
                    gbest_metrics = dict(met)

            # Compute Swarm Diversity
            diversity = self.compute_population_diversity(positions)
            diversity_history.append(diversity)

            if self.check_premature_convergence(diversity, it, iterations):
                premature_convergence_flag = True

            mean_fitness = round(float(np.mean(fitness_scores)), 5)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            convergence_history.append(
                ConvergencePoint(
                    iteration=it,
                    best_fitness=gbest_fitness,
                    mean_fitness=mean_fitness,
                    diversity=diversity,
                    best_parameters=self.space.to_dict(gbest_position),
                    exploration_rate=round(w, 3), # Inertia acts as exploration indicator
                    elapsed_time_ms=round(elapsed_ms, 2)
                ).__dict__
            )

            # Check Termination
            if it == iterations:
                break

            # 3. Update Velocities and Positions
            for particle in swarm:
                for d in range(dim):
                    r1 = random.random()
                    r2 = random.random()
                    
                    cog = cognitive_coeff * r1 * (particle.pbest_position[d] - particle.position[d])
                    soc = social_coeff * r2 * (gbest_position[d] - particle.position[d])
                    
                    new_vel = w * particle.velocity[d] + cog + soc
                    # Clamp velocity to v_max
                    new_vel = max(-v_max[d], min(v_max[d], new_vel))
                    particle.velocity[d] = new_vel

                    # Update position
                    particle.position[d] += new_vel

                # Clamp and repair constraints
                particle.position = self.constraints.repair(particle.position)

        total_runtime = time.perf_counter() - start_time

        return OptimizerResult(
            algorithm="Particle Swarm Optimization (PSO)",
            best_parameters=self.space.to_dict(gbest_position),
            best_fitness=gbest_fitness,
            metrics=gbest_metrics,
            runtime_seconds=round(total_runtime, 4),
            convergence_history=convergence_history,
            diversity_history=diversity_history,
            premature_convergence_detected=premature_convergence_flag,
            iterations_run=iterations,
            population_size=population_size,
            random_seed=self.seed
        )

    @property
    def parameters_spec(self):
        return self.space.parameters
