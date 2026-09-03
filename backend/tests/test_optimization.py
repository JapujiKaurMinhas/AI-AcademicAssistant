import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from optimization.search_space import SearchSpace, ParameterSpec
from optimization.constraints import ConstraintHandler
from optimization.fitness import FitnessEvaluator, FitnessWeights
from optimization.evaluation import RetrievalEvaluator, DEFAULT_BENCHMARK_DOCUMENT
from optimization.baseline import BaselineOptimizer
from optimization.ga import GeneticAlgorithmOptimizer
from optimization.pso import ParticleSwarmOptimizer
from optimization.gwo import GreyWolfOptimizer
from optimization.nsga2 import NSGA2Optimizer, Individual
from optimization.hybrid_ga_pso import HybridGAPSOOptimizer
from optimization.active_config import get_active_config, set_active_config, reset_to_default
from optimization.sensitivity import SensitivityAnalyzer
from optimization.ablation import AblationStudyRunner
from main import app

client = TestClient(app)

# 1. Search Space Tests
def test_search_space_initialization_and_bounds():
    space = SearchSpace()
    assert space.dimension == 5
    assert space.names == ["chunk_size", "chunk_overlap", "top_k", "similarity_threshold", "context_token_budget"]
    
    vec = space.sample_vector()
    assert len(vec) == 5
    # Overlap must be < chunk_size
    assert vec[1] < vec[0]

    # Normalization / Denormalization roundtrip
    norm = space.normalize_vector(vec)
    for v in norm:
        assert 0.0 <= v <= 1.0
    denorm = space.denormalize_vector(norm)
    assert len(denorm) == 5

# 2. Constraint Handling Tests
def test_constraint_validation_and_repair():
    space = SearchSpace()
    handler = ConstraintHandler(space)
    
    # An invalid vector with overlap > chunk_size
    invalid_vec = [500, 600, 0, 1.5, 9000]
    valid, violations = handler.validate(invalid_vec)
    assert not valid
    assert len(violations) >= 2
    
    # Repair
    repaired = handler.repair(invalid_vec)
    valid_after, violations_after = handler.validate(repaired)
    assert valid_after
    assert repaired[1] <= 0.5 * repaired[0]
    assert repaired[2] >= 1

# 3. Fitness Calculation Tests
def test_fitness_calculation():
    weights = FitnessWeights(w_retrieval=0.4, w_semantic=0.3, w_coverage=0.1, w_latency=0.1, w_tokens=0.1)
    evaluator = FitnessEvaluator(weights)
    
    metrics = {
        "retrieval_relevance": 0.85,
        "semantic_similarity": 0.90,
        "context_coverage": 0.75,
        "latency_ms": 25.0,
        "estimated_tokens": 1200
    }
    fit = evaluator.evaluate(metrics, penalty=0.0)
    assert isinstance(fit, float)
    assert fit > 0.0

    # Test multi-objective
    objs = evaluator.evaluate_multi_objective(metrics)
    assert len(objs) == 3
    assert objs[0] < 0  # Quality is negated for minimization
    assert objs[1] == 25.0 # Latency ms
    assert objs[2] == 1200 # Tokens

# 4. Centralized Evaluation Engine Tests
def test_evaluation_engine():
    evaluator = RetrievalEvaluator(document_text=DEFAULT_BENCHMARK_DOCUMENT)
    res = evaluator.evaluate_candidate(
        chunk_size=800,
        chunk_overlap=100,
        top_k=3,
        similarity_threshold=0.20,
        context_token_budget=3000
    )
    assert "retrieval_relevance" in res
    assert "retrieval_quality" in res
    assert "latency_ms" in res
    assert "estimated_tokens" in res
    assert res["retrieval_relevance"] > 0.0

    # Test caching
    res2 = evaluator.evaluate_candidate(
        chunk_size=800,
        chunk_overlap=100,
        top_k=3,
        similarity_threshold=0.20,
        context_token_budget=3000
    )
    assert res2["cached"] is True

# 5. Baseline Evaluation Tests
def test_baseline_optimizer():
    space = SearchSpace()
    evaluator = RetrievalEvaluator()
    fitness = FitnessEvaluator()
    constraints = ConstraintHandler(space)
    
    baseline = BaselineOptimizer(space, constraints, evaluator, fitness)
    res = baseline.optimize()
    assert res.algorithm.startswith("Baseline")
    assert res.best_fitness is not None
    assert len(res.convergence_history) == 1

# 6. GA Optimizer Tests
def test_genetic_algorithm():
    space = SearchSpace()
    evaluator = RetrievalEvaluator()
    fitness = FitnessEvaluator()
    constraints = ConstraintHandler(space)
    
    ga = GeneticAlgorithmOptimizer(space, constraints, evaluator, fitness, random_seed=42)
    res = ga.optimize(population_size=6, iterations=3)
    assert res.algorithm == "Genetic Algorithm (GA)"
    assert len(res.convergence_history) == 3
    assert res.best_fitness is not None
    assert len(res.diversity_history) == 3

# 7. PSO Optimizer Tests
def test_particle_swarm_optimization():
    space = SearchSpace()
    evaluator = RetrievalEvaluator()
    fitness = FitnessEvaluator()
    constraints = ConstraintHandler(space)
    
    pso = ParticleSwarmOptimizer(space, constraints, evaluator, fitness, random_seed=42)
    res = pso.optimize(population_size=6, iterations=3)
    assert res.algorithm == "Particle Swarm Optimization (PSO)"
    assert len(res.convergence_history) == 3
    assert res.best_fitness is not None

# 8. GWO Optimizer Tests
def test_grey_wolf_optimizer():
    space = SearchSpace()
    evaluator = RetrievalEvaluator()
    fitness = FitnessEvaluator()
    constraints = ConstraintHandler(space)
    
    gwo = GreyWolfOptimizer(space, constraints, evaluator, fitness, random_seed=42)
    res = gwo.optimize(population_size=6, iterations=3)
    assert res.algorithm == "Grey Wolf Optimizer (GWO)"
    assert len(res.convergence_history) == 3

# 9. NSGA-II Multi-Objective & Pareto Front Tests
def test_nsga2_optimizer():
    space = SearchSpace()
    evaluator = RetrievalEvaluator()
    fitness = FitnessEvaluator()
    constraints = ConstraintHandler(space)
    
    nsga = NSGA2Optimizer(space, constraints, evaluator, fitness, random_seed=42)
    res = nsga.optimize(population_size=8, iterations=3)
    assert res.algorithm.startswith("NSGA-II")
    assert res.pareto_front is not None
    assert len(res.pareto_front) > 0
    # Every solution in Pareto front should have quality, latency, tokens
    for sol in res.pareto_front:
        assert "quality" in sol
        assert "latency_ms" in sol
        assert "tokens" in sol
        assert "parameters" in sol

# 10. Hybrid GA + PSO Tests
def test_hybrid_ga_pso():
    space = SearchSpace()
    evaluator = RetrievalEvaluator()
    fitness = FitnessEvaluator()
    constraints = ConstraintHandler(space)
    
    hybrid = HybridGAPSOOptimizer(space, constraints, evaluator, fitness, random_seed=42)
    res = hybrid.optimize(population_size=6, iterations=4, ga_ratio=0.5)
    assert res.algorithm == "Hybrid GA + PSO"
    assert len(res.convergence_history) == 4

# 11. Active Configuration & QA Integration
def test_active_retrieval_configuration():
    reset_to_default()
    cfg = get_active_config()
    assert cfg.mode == "default"
    assert cfg.chunk_size == 800
    
    # Update to optimized
    set_active_config(chunk_size=650, chunk_overlap=90, top_k=5, similarity_threshold=0.35, context_token_budget=2500, mode="optimized", algorithm_source="GA Run #1")
    updated = get_active_config()
    assert updated.mode == "optimized"
    assert updated.chunk_size == 650
    assert updated.top_k == 5

# 12. API Endpoints Tests
def test_optimization_api_endpoints():
    # 1. Search Space
    r = client.get("/api/optimization/search-space")
    assert r.status_code == 200
    data = r.json()
    assert "decision_variables" in data
    assert "constraints" in data
    
    # 2. Algorithms
    r = client.get("/api/optimization/algorithms")
    assert r.status_code == 200
    assert len(r.json()["algorithms"]) == 6

    # 3. Active Config GET & POST
    r = client.get("/api/optimization/active-config")
    assert r.status_code == 200
    
    r = client.post("/api/optimization/active-config", json={
        "chunk_size": 720,
        "chunk_overlap": 80,
        "top_k": 4,
        "similarity_threshold": 0.25,
        "context_token_budget": 2800,
        "mode": "optimized"
    })
    assert r.status_code == 200
    assert r.json()["active_config"]["chunk_size"] == 720

    # 4. Run Optimization (GA short run)
    r = client.post("/api/optimization/run", json={
        "algorithm": "ga",
        "population_size": 6,
        "iterations": 2,
        "random_seed": 42
    })
    assert r.status_code == 200
    run_data = r.json()
    assert "experiment_id" in run_data
    exp_id = run_data["experiment_id"]

    # 5. Fetch Experiment
    r = client.get(f"/api/optimization/experiments/{exp_id}")
    assert r.status_code == 200
    assert r.json()["id"] == exp_id

    # 6. Export Experiment (JSON & CSV)
    r = client.get(f"/api/optimization/export/{exp_id}?format=json")
    assert r.status_code == 200
    
    r = client.get(f"/api/optimization/export/{exp_id}?format=csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
