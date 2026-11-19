"""
Microbial Evolution Simulation Engine - Interactive Virtual Lab Edition.
"""
import uuid
import random
import numpy as np

from .genetic_algorithm import (
    crossover,
    fitness as ga_fitness,
    genome_from_resistance,
    mutate as ga_mutate,
    phenotype_resistance,
    population_diversity,
    random_genome,
    tournament_select,
)

SPECIES_PROFILES = {
    "ecoli": {"label": "E. coli", "base_growth": 0.32, "base_mutation": 0.01},
    "mrsa": {"label": "MRSA", "base_growth": 0.22, "base_mutation": 0.02},
    "pseudomonas": {"label": "Pseudomonas", "base_growth": 0.27, "base_mutation": 0.015},
    "klebsiella": {"label": "K. pneumoniae", "base_growth": 0.3, "base_mutation": 0.018},
    "acinetobacter": {"label": "Acinetobacter", "base_growth": 0.24, "base_mutation": 0.03},
    "enterococcus": {"label": "E. faecium", "base_growth": 0.26, "base_mutation": 0.012},
    "streptococcus": {"label": "S. pneumoniae", "base_growth": 0.28, "base_mutation": 0.008},
    "salmonella": {"label": "S. enterica", "base_growth": 0.25, "base_mutation": 0.014},
    "gonorrhoeae": {"label": "N. gonorrhoeae", "base_growth": 0.24, "base_mutation": 0.02},
    "enterobacter": {"label": "E. cloacae", "base_growth": 0.29, "base_mutation": 0.02},
    "haemophilus": {"label": "H. influenzae", "base_growth": 0.26, "base_mutation": 0.01},
}

# Real-world mapped scenarios (objectives): hospital surface (MRSA) and UTI (E. coli)
SCENARIO_PRESETS = {
    "hospital_surface_mrsa": {
        "label": "Hospital Surface Infection (MRSA)",
        "description": "High-touch hospital surface contamination with methicillin-resistant S. aureus under cleaning/disinfection pressure.",
        "species": "mrsa",
        "antibiotic": "vancomycin",
        "initial_population": 140,
        "antibiotic_level": 0.55,
        "mutation_rate": 0.06,
        "mutation_strength": 0.14,
        "growth_rate": 0.24,
        "hgt_rate": 0.03,
        "grid_size": 40,
    },
    "uti_ecoli": {
        "label": "Urinary Tract Infection (E. coli)",
        "description": "Urinary tract infection scenario with E. coli exposed to antibiotic therapy and host/environment selective pressure.",
        "species": "ecoli",
        "antibiotic": "nitrofurantoin",
        "initial_population": 160,
        "antibiotic_level": 0.45,
        "mutation_rate": 0.05,
        "mutation_strength": 0.12,
        "growth_rate": 0.32,
        "hgt_rate": 0.025,
        "grid_size": 40,
    },
}

SUSCEPTIBLE, INTERMEDIATE, RESISTANT, HIGHLY_RESISTANT = 0, 1, 2, 3

# Horizontal gene transfer (conjugation) parameters:
# a cell must be at least this resistant to act as a plasmid donor, and the
# recipient's resistance moves this fraction of the way toward the donor.
HGT_MIN_RESISTANCE = 0.5
HGT_TRANSFER_FRACTION = 0.5


def classify(resistance):
    if resistance < 0.25:
        return SUSCEPTIBLE
    if resistance < 0.50:
        return INTERMEDIATE
    if resistance < 0.75:
        return RESISTANT
    return HIGHLY_RESISTANT


class Cell:
    __slots__ = ("x", "y", "resistance", "alive", "mutations", "genome", "fitness")

    def __init__(self, x, y, resistance, mutations=0, genome=None):
        self.x = x
        self.y = y
        self.genome = genome if genome is not None else genome_from_resistance(resistance)
        self.resistance = float(np.clip(phenotype_resistance(self.genome), 0.0, 1.0))
        self.alive = True
        self.mutations = mutations
        self.fitness = 0.0


class SimulationEngine:
    def __init__(
        self,
        species="ecoli",
        grid_size=40,
        initial_population=120,
        mutation_rate=0.05,
        mutation_strength=0.1,
        antibiotic_level=0.5,
        growth_rate=0.3,
        simulation_speed=1.0,
        hgt_rate=0.02,
        scenario=None,
    ):
        self.id = str(uuid.uuid4())
        self.scenario = scenario if scenario in SCENARIO_PRESETS else None
        self.species = species if species in SPECIES_PROFILES else "ecoli"
        profile = SPECIES_PROFILES[self.species]

        self.grid_size = int(grid_size)
        self.mutation_rate = float(mutation_rate)
        self.mutation_strength = float(mutation_strength) * 4.0

        self.antibiotic_level = float(antibiotic_level)
        self.growth_rate = float(growth_rate) if growth_rate else profile["base_growth"]
        self.simulation_speed = float(simulation_speed)
        self.hgt_rate = float(hgt_rate)

        self.generation = 0
        self.mutation_count = 0
        self.death_count = 0
        self.hgt_count = 0
        self.ga_selection_events = 0
        self.ga_crossover_events = 0
        self.ga_mutation_events = 0
        self.history = []
        self.interventions_log = []  # Tracks manual lab actions

        self.antibiotic_field = self._init_antibiotic_field()
        self.cells = []
        self.max_population = max(int(initial_population) * 12, 800)

        occupied = set()
        while len(self.cells) < int(initial_population) and len(occupied) < self.grid_size**2:
            x = random.randint(0, self.grid_size - 1)
            y = random.randint(0, self.grid_size - 1)
            if (x, y) not in occupied:
                occupied.add((x, y))
                seed_res = self._seed_resistance()
                self.cells.append(Cell(x, y, seed_res, genome=random_genome()))

        self.running = False

    def _seed_resistance(self):
        """Sample an initial resistance value for a freshly seeded cell.

        Every cell starts in the low susceptible range so any resistance that
        appears later is the result of mutation and selection pressure, not an
        initial condition.
        """
        return random.uniform(0.0, 0.10)

    def _init_antibiotic_field(self):
        size = self.grid_size
        yy, xx = np.mgrid[0:size, 0:size]
        cx, cy = size / 2, size / 2
        dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (size / 2)
        field = self.antibiotic_level * np.clip(1.0 - dist * 0.6, 0.1, 1.0)
        return field

    def apply_treatment(self, intensity, center_x=None, center_y=None, drug_name="Custom Treatment"):
        """
        LAB FEATURE: Allows the user to drop a targeted antibiotic disk 
        or change drug concentration anywhere on the grid mid-simulation.
        """
        intensity = float(intensity)
        size = self.grid_size
        
        if center_x is None or center_y is None:
            cx, cy = size / 2, size / 2
        else:
            cx, cy = float(center_x), float(center_y)


        yy, xx = np.mgrid[0:size, 0:size]
        dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (size / 2)
        
        # Create a localized diffusion gradient ring (Kirby-Bauer simulation).
        # Concentration can exceed 1.0 to simulate a high-dose shock dose —
        # cells with resistance below the local concentration will die.
        new_pocket = intensity * np.clip(1.0 - dist * 0.8, 0.0, 1.0)
        
        # Blend with current antibiotic field (allow supra-MIC dosing, cap at 2.0)
        self.antibiotic_field = np.clip(self.antibiotic_field + new_pocket, 0.0, 2.0)
        
        self.interventions_log.append({
            "generation": self.generation,
            "action": "apply_treatment",
            "drug": drug_name,
            "intensity": intensity,
            "coordinates": (cx, cy)
        })
        return self.get_state()

    def _diffuse_antibiotic(self):
        kernel_sum = (
            np.roll(self.antibiotic_field, 1, axis=0)
            + np.roll(self.antibiotic_field, -1, axis=0)
            + np.roll(self.antibiotic_field, 1, axis=1)
            + np.roll(self.antibiotic_field, -1, axis=1)
        )
        self.antibiotic_field = 0.5 * self.antibiotic_field + 0.125 * kernel_sum
        # Allow natural decay if unforced, keeping baseline flexible for lab resets
        self.antibiotic_field = np.clip(self.antibiotic_field, 0.1, 2.0)

    def _horizontal_gene_transfer(self, cells):
        """LAB FEATURE: conjugation (plasmid/gene transfer).
        Spreads resistance laterally by transferring advantageous genome segments
        from donor to recipient and recomputing phenotype resistance.
        """
        if self.hgt_rate <= 0 or len(cells) < 2:
            return 0

        occupied = {(c.x, c.y): c for c in cells}
        donor_snapshot = {id(c): (c.resistance, list(c.genome)) for c in cells}
        transfers = 0
        grid = self.grid_size

        for donor in cells:
            base_res, base_genome = donor_snapshot.get(id(donor), (donor.resistance, list(donor.genome)))
            if base_res < HGT_MIN_RESISTANCE:
                continue
            if random.random() > self.hgt_rate:
                continue

            candidates = [
                (donor.x + dx, donor.y + dy)
                for dx in (-1, 0, 1)
                for dy in (-1, 0, 1)
                if not (dx == 0 and dy == 0)
            ]
            random.shuffle(candidates)

            for nx, ny in candidates:
                if 0 <= nx < grid and 0 <= ny < grid:
                    receiver = occupied.get((nx, ny))
                    if receiver is not None and receiver.resistance < base_res:
                        # Gene/plasmid segment transfer + phenotype update.
                        for i, gval in enumerate(base_genome):
                            if random.random() < 0.35 and gval > receiver.genome[i]:
                                receiver.genome[i] = float(np.clip(
                                    receiver.genome[i] + (gval - receiver.genome[i]) * HGT_TRANSFER_FRACTION,
                                    0.0, 1.0
                                ))
                        receiver.resistance = phenotype_resistance(receiver.genome)
                        transfers += 1
                        break

        return transfers

    def step(self):
        self.generation += 1
        self._diffuse_antibiotic()

        survivors = []
        occupied = set()
        deaths_this_gen = 0
        mutations_this_gen = 0
        selection_events = 0
        crossover_events = 0

        for cell in self.cells:
            if not cell.alive:
                continue

            local_ab = float(self.antibiotic_field[cell.y, cell.x])
            # Recompute phenotype fitness from genome under current environment.
            cell.resistance = phenotype_resistance(cell.genome)
            cell.fitness = ga_fitness(cell.genome, local_ab, self.growth_rate)
            survival_chance = float(np.clip(1.0 - max(0.0, local_ab - cell.resistance), 0.0, 1.0))

            if random.random() > survival_chance:
                cell.alive = False
                deaths_this_gen += 1
                continue

            if (cell.x, cell.y) not in occupied:
                occupied.add((cell.x, cell.y))
                survivors.append(cell)
            else:
                deaths_this_gen += 1

        new_cells = []
        if survivors:
            fitness_pool = [
                (c.genome, ga_fitness(c.genome, float(self.antibiotic_field[c.y, c.x]), self.growth_rate))
                for c in survivors
            ]
        else:
            fitness_pool = []

        for cell in survivors:
            new_cells.append(cell)

            if random.random() < self.growth_rate and len(new_cells) < self.max_population:
                neighbors = [
                    (cell.x + dx, cell.y + dy)
                    for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                    if not (dx == 0 and dy == 0)
                ]
                random.shuffle(neighbors)

                for nx, ny in neighbors:
                    if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                        if (nx, ny) not in occupied:
                            # Genetic algorithm reproduction: selection + crossover + mutation
                            mate_genome = tournament_select(fitness_pool, k=3) if len(fitness_pool) > 1 else list(cell.genome)
                            selection_events += 1 if len(fitness_pool) > 1 else 0
                            child_genome, did_cross = crossover(cell.genome, mate_genome, rate=0.75)
                            crossover_events += 1 if did_cross else 0

                            local_ab_child = float(self.antibiotic_field[ny, nx])
                            pressure = max(0.0, local_ab_child - phenotype_resistance(child_genome))
                            adaptive_rate = min(0.95, self.mutation_rate * (2.0 + pressure * 1.5))
                            adaptive_strength = self.mutation_strength * (1.0 + pressure * 0.5)
                            child_genome, did_mutate = ga_mutate(child_genome, adaptive_rate, adaptive_strength)

                            child_mutations = cell.mutations + (1 if did_mutate else 0)
                            mutations_this_gen += 1 if did_mutate else 0

                            child = Cell(nx, ny, 0.0, child_mutations, genome=child_genome)
                            child.fitness = ga_fitness(child.genome, local_ab_child, self.growth_rate)
                            occupied.add((nx, ny))
                            new_cells.append(child)
                            break

        self.cells = new_cells

        hgt_events_this_gen = self._horizontal_gene_transfer(self.cells)
        self.hgt_count += hgt_events_this_gen
        self.death_count += deaths_this_gen
        self.mutation_count += mutations_this_gen
        self.ga_selection_events += selection_events
        self.ga_crossover_events += crossover_events
        self.ga_mutation_events += mutations_this_gen

        snapshot = self._build_snapshot(
            deaths_this_gen, mutations_this_gen, hgt_events_this_gen,
            selection_events=selection_events, crossover_events=crossover_events
        )
        self.history.append(snapshot)
        return snapshot

    def _build_snapshot(self, deaths_this_gen, mutations_this_gen, hgt_events_this_gen=0, selection_events=0, crossover_events=0):
        population = len(self.cells)
        if population > 0:
            resistances = np.array([c.resistance for c in self.cells])
            fitnesses = np.array([getattr(c, "fitness", 0.0) for c in self.cells], dtype=float)
            avg_resistance = float(resistances.mean())
            resistant_frac = float((resistances >= 0.75).mean())
            mean_fitness = float(fitnesses.mean()) if fitnesses.size else 0.0
            best_fitness = float(fitnesses.max()) if fitnesses.size else 0.0
            diversity = population_diversity([c.genome for c in self.cells])
        else:
            avg_resistance = 0.0
            resistant_frac = 0.0
            mean_fitness = 0.0
            best_fitness = 0.0
            diversity = 0.0

        survival_rate = 1.0 - (
            deaths_this_gen / max(1, deaths_this_gen + population)
        )

        hotspot_count = self._count_hotspots()

        return {
            "generation": self.generation,
            "population": population,
            "avg_resistance": round(avg_resistance, 4),
            "resistant_fraction": round(resistant_frac, 4),
            "deaths": deaths_this_gen,
            "mutations": mutations_this_gen,
            "hgt_events": hgt_events_this_gen,
            "cumulative_deaths": self.death_count,
            "cumulative_mutations": self.mutation_count,
            "cumulative_hgt_events": self.hgt_count,
            "survival_rate": round(survival_rate, 4),
            "hotspot_count": hotspot_count,
            "dominant_colony": classify(avg_resistance),
            "ga_mean_fitness": round(mean_fitness, 4),
            "ga_best_fitness": round(best_fitness, 4),
            "ga_diversity": round(diversity, 4),
            "ga_selection_events": int(selection_events),
            "ga_crossover_events": int(crossover_events),
            "ga_cumulative_selection_events": int(self.ga_selection_events),
            "ga_cumulative_crossover_events": int(self.ga_crossover_events),
            "ga_cumulative_mutation_events": int(self.ga_mutation_events),
        }

    def _count_hotspots(self):
        threshold = 0.6
        grid = np.zeros((self.grid_size, self.grid_size))
        for c in self.cells:
            if c.resistance >= 0.75:
                grid[c.y, c.x] += 1
        hot = (self.antibiotic_field > threshold) & (grid > 0)
        return int(hot.sum())

    def get_cells_payload(self):
        return [
            {
                "id": idx + 1,
                "x": c.x,
                "y": c.y,
                "r": round(c.resistance, 3),
                "cls": classify(c.resistance),
                "alive": True,
                "generation_born": self.generation,
                "mutation_count": c.mutations,
                "growth_rate": round(self.growth_rate, 3),
                "parent_id": None,
                "fitness": round(float(getattr(c, "fitness", 0.0)), 3),
                "genome_signature": round(float(np.mean(c.genome)) if getattr(c, "genome", None) else c.resistance, 3),
            }
            for idx, c in enumerate(self.cells)
        ]

    def get_antibiotic_field_payload(self, downsample=1):
        field = self.antibiotic_field
        if downsample > 1:
            field = field[::downsample, ::downsample]
        return np.round(field, 3).tolist()

    def get_state(self):
        latest = self.history[-1] if self.history else self._build_snapshot(0, 0, 0)
        scenario_meta = SCENARIO_PRESETS.get(self.scenario, None)
        return {
            "id": self.id,
            "species": self.species,
            "scenario": self.scenario,
            "scenario_label": scenario_meta["label"] if scenario_meta else None,
            "grid_size": self.grid_size,
            "generation": self.generation,
            "cells": self.get_cells_payload(),
            "antibiotic_field": self.get_antibiotic_field_payload(downsample=2),
            "stats": latest,
            "interventions_log": self.interventions_log,
            "ga_enabled": True,
            "ga_model": "Genome-based GA (selection, crossover, mutation, fitness under antibiotic pressure)",
        }

    def config_metadata(self):
        scenario_meta = SCENARIO_PRESETS.get(self.scenario, None)
        return {
            "species": self.species,
            "scenario": self.scenario,
            "scenario_label": scenario_meta["label"] if scenario_meta else None,
            "scenario_description": scenario_meta["description"] if scenario_meta else None,
            "grid_size": self.grid_size,
            "mutation_rate": self.mutation_rate / 4.0 if self.mutation_strength else self.mutation_rate,
            "mutation_strength": self.mutation_strength / 4.0,
            "antibiotic_level": self.antibiotic_level,
            "growth_rate": self.growth_rate,
            "simulation_speed": self.simulation_speed,
            "hgt_rate": self.hgt_rate,
            "ga_enabled": True,
        }