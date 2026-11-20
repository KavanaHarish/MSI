"""
Genetic Algorithm utilities for modeling bacterial evolutionary dynamics.

Each cell carries a small genome representing resistance-related traits.
Fitness is evaluated against local antibiotic pressure and growth potential.
Selection, crossover, and mutation operators produce offspring genomes that
adapt over generations under selective pressure.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import numpy as np


GENOME_LENGTH = 8  # genes: resistance mechanisms, efflux, membrane, repair, etc.


@dataclass
class GAStats:
    generation: int
    mean_fitness: float
    best_fitness: float
    diversity: float
    selection_events: int
    crossover_events: int
    mutation_events: int


def random_genome(rng: random.Random | None = None) -> List[float]:
    r = rng or random
    # Start with low-to-moderate susceptibility and standing variation so
    # selection has material to act on under antibiotic pressure.
    return [float(np.clip(r.uniform(0.02, 0.22) + r.gauss(0, 0.02), 0.0, 1.0)) for _ in range(GENOME_LENGTH)]


def genome_from_resistance(resistance: float, rng: random.Random | None = None) -> List[float]:
    r = rng or random
    base = float(np.clip(resistance, 0.0, 1.0))
    return [float(np.clip(base * r.uniform(0.6, 1.4) + r.uniform(0.0, 0.05), 0.0, 1.0)) for _ in range(GENOME_LENGTH)]


def phenotype_resistance(genome: Sequence[float]) -> float:
    if not genome:
        return 0.0
    g = np.asarray(genome, dtype=float)
    # Weighted expression: core resistance genes + efflux/membrane/repair contributions.
    weights = np.array([0.22, 0.18, 0.14, 0.12, 0.12, 0.08, 0.08, 0.06], dtype=float)
    w = weights[: len(g)]
    expr = float(np.dot(g[: len(w)], w) / (w.sum() or 1.0))
    # Synergy bonus when multiple mechanisms co-occur.
    synergy = float(np.mean(np.sort(g)[-3:])) * 0.08 if len(g) >= 3 else 0.0
    return float(np.clip(expr + synergy, 0.0, 1.0))


def fitness(genome: Sequence[float], local_antibiotic: float, growth_rate: float) -> float:
    res = phenotype_resistance(genome)
    survival = 1.0 - max(0.0, float(local_antibiotic) - res)
    # Mild metabolic cost for very high resistance expression.
    cost = 0.04 * float(np.mean(genome)) if genome else 0.0
    return float(np.clip(survival * (0.55 + 0.45 * float(growth_rate)) - cost, 0.0, 1.5))


def tournament_select(
    candidates: Sequence[Tuple[Sequence[float], float]],
    k: int = 3,
    rng: random.Random | None = None,
) -> Sequence[float]:
    """Fitness-proportionate tournament selection."""
    r = rng or random
    if not candidates:
        return random_genome(r)
    k = max(1, min(k, len(candidates)))
    contenders = r.sample(list(candidates), k) if len(candidates) >= k else list(candidates)
    contenders.sort(key=lambda item: item[1], reverse=True)
    # Probabilistic pick biased to best contender.
    if len(contenders) == 1 or r.random() < 0.75:
        return contenders[0][0]
    return contenders[1][0]


def crossover(parent_a: Sequence[float], parent_b: Sequence[float], rate: float = 0.7, rng: random.Random | None = None):
    r = rng or random
    a = list(parent_a)
    b = list(parent_b)
    if len(a) != len(b):
        n = min(len(a), len(b))
        a, b = a[:n], b[:n]
    if not a:
        return random_genome(r), False
    if r.random() > rate:
        return list(a), False
    # Uniform crossover with one-point fallback.
    if r.random() < 0.5 and len(a) > 2:
        point = r.randint(1, len(a) - 1)
        child = a[:point] + b[point:]
    else:
        child = [a[i] if r.random() < 0.5 else b[i] for i in range(len(a))]
    return [float(np.clip(v, 0.0, 1.0)) for v in child], True


def mutate(genome: Sequence[float], rate: float, strength: float, rng: random.Random | None = None):
    r = rng or random
    child = list(genome)
    mutated = False
    for i in range(len(child)):
        if r.random() < rate:
            delta = r.gauss(0.0, max(0.001, strength * 0.35))
            # Bias toward gain under pressure is applied by caller through strength/rate; keep general here.
            child[i] = float(np.clip(child[i] + delta, 0.0, 1.0))
            mutated = True
    # Rare large-effect mutation (e.g. plasmid acquisition / key mutation)
    if r.random() < rate * 0.15:
        idx = r.randrange(len(child)) if child else 0
        if child:
            child[idx] = float(np.clip(child[idx] + r.uniform(0.1, 0.4) * strength, 0.0, 1.0))
            mutated = True
    return child, mutated


def population_diversity(genomes: Iterable[Sequence[float]]) -> float:
    arr = np.array(list(genomes), dtype=float)
    if arr.size == 0 or arr.shape[0] < 2:
        return 0.0
    # Mean pairwise L1 distance normalized to [0,1].
    dists = []
    # Sample for efficiency on larger populations.
    idx = np.arange(arr.shape[0])
    if len(idx) > 60:
        rng = np.random.default_rng(0)
        idx = rng.choice(idx, size=60, replace=False)
    sample = arr[idx]
    for i in range(len(sample)):
        for j in range(i + 1, len(sample)):
            dists.append(np.mean(np.abs(sample[i] - sample[j])))
    if not dists:
        return 0.0
    return float(np.clip(np.mean(dists), 0.0, 1.0))
