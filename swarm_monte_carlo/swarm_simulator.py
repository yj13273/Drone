"""Compare swarm routing strategies with a Monte Carlo mission simulation.

Run from the repository root:
    python swarm_monte_carlo/swarm_simulator.py --sizes 10,20,40,80 --runs 5000
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from statistics import fmean
from typing import Dict, List, Optional, Tuple


STRATEGIES = (
    "single_route",
    "multiple_routes",
    "decoy_lead",
    "distributed_routing",
)


@dataclass
class Scenario:
    """Initial conditions for a mission; probability fields must be between 0 and 1."""

    radar_detection_probability: float = 0.45
    sam_kill_probability: float = 0.35
    ew_effectiveness: float = 0.40
    communication_loss_probability: float = 0.12
    weather_severity: float = 0.25

    route_segments: int = 4
    required_payload_fraction: float = 0.55
    target_coverage_goal: float = 0.70
    routes_for_split_swarm: int = 3

    drone_cost: float = 100_000.0
    decoy_cost_multiplier: float = 0.35
    lost_drone_recovery_cost: float = 15_000.0
    failed_mission_penalty: float = 500_000.0
    probability_uncertainty: float = 0.08


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def sampled_probability(mean: float, uncertainty: float, rng: random.Random) -> float:
    """Sample one trial's condition around its configured initial value."""
    return clamp(rng.gauss(mean, uncertainty))


def route_exposure(
    strategy: str,
    drone_index: int,
    swarm_size: int,
    scenario: Scenario,
    rng: random.Random,
) -> Tuple[float, bool, float]:
    """Return (threat_multiplier, is_decoy, launch_cost_multiplier)."""
    if strategy == "single_route":
        return 1.0, False, 1.0

    if strategy == "multiple_routes":
        route_number = drone_index % max(1, scenario.routes_for_split_swarm)
        exposure = 0.78 + route_number * 0.12 + rng.uniform(-0.05, 0.05)
        return exposure, False, 1.0

    if strategy == "decoy_lead":
        decoy_count = max(1, math.ceil(swarm_size * 0.20))
        is_decoy = drone_index < decoy_count
        return (1.30 if is_decoy else 0.78), is_decoy, (
            scenario.decoy_cost_multiplier if is_decoy else 1.0
        )

    if strategy == "distributed_routing":
        return min(rng.uniform(0.62, 1.15) for _ in range(4)), False, 1.0

    raise ValueError(f"Unknown strategy: {strategy}")


def simulate_trial(
    strategy: str, swarm_size: int, scenario: Scenario, rng: random.Random
) -> Dict[str, float]:
    """Run one mission using a new random draw of all Monte Carlo variables."""
    radar = sampled_probability(
        scenario.radar_detection_probability, scenario.probability_uncertainty, rng
    )
    sam = sampled_probability(scenario.sam_kill_probability, scenario.probability_uncertainty, rng)
    ew = sampled_probability(scenario.ew_effectiveness, scenario.probability_uncertainty, rng)
    communication_loss = sampled_probability(
        scenario.communication_loss_probability, scenario.probability_uncertainty, rng
    )
    weather = sampled_probability(scenario.weather_severity, scenario.probability_uncertainty, rng)

    surviving_payload = 0
    payload_launched = 0
    lost_drones = 0
    launch_cost = 0.0

    for drone_index in range(swarm_size):
        exposure, is_decoy, cost_multiplier = route_exposure(
            strategy, drone_index, swarm_size, scenario, rng
        )
        launch_cost += scenario.drone_cost * cost_multiplier
        if not is_decoy:
            payload_launched += 1

        alive = True
        connected = True
        for _ in range(scenario.route_segments):
            if not alive:
                break

            if rng.random() < clamp(0.015 + weather * 0.10):
                alive = False
                break

            if rng.random() < clamp(communication_loss + weather * 0.08):
                connected = False

            effective_exposure = exposure
            if strategy == "distributed_routing":
                effective_exposure *= 0.82 if connected else 1.18

            detection_probability = clamp(
                radar * effective_exposure * (1.0 - ew * 0.55) * (1.0 - weather * 0.18)
            )
            if strategy == "decoy_lead" and not is_decoy:
                detection_probability *= 0.72

            if rng.random() < detection_probability:
                kill_probability = clamp(sam * effective_exposure * (1.0 - ew * 0.45))
                if not connected:
                    kill_probability = clamp(kill_probability * 1.15)
                if rng.random() < kill_probability:
                    alive = False

        if alive and not is_decoy:
            surviving_payload += 1
        elif not alive:
            lost_drones += 1

    required_payload = max(1, math.ceil(payload_launched * scenario.required_payload_fraction))
    coverage = surviving_payload / max(1, payload_launched)
    mission_complete = (
        surviving_payload >= required_payload and coverage >= scenario.target_coverage_goal
    )
    mission_cost = launch_cost + lost_drones * scenario.lost_drone_recovery_cost
    if not mission_complete:
        mission_cost += scenario.failed_mission_penalty

    return {
        "surviving_drones": float(surviving_payload),
        "mission_complete": float(mission_complete),
        "target_coverage": coverage,
        "mission_cost": mission_cost,
    }


def simulate(
    strategy: str, swarm_size: int, runs: int, scenario: Scenario, seed: int
) -> Dict[str, float]:
    rng = random.Random(seed)
    trials = [simulate_trial(strategy, swarm_size, scenario, rng) for _ in range(runs)]
    return {
        "strategy": strategy,
        "swarm_size": swarm_size,
        "runs": runs,
        "mean_surviving_drones": round(fmean(x["surviving_drones"] for x in trials), 3),
        "mission_completion_probability": round(fmean(x["mission_complete"] for x in trials), 4),
        "mean_target_coverage": round(fmean(x["target_coverage"] for x in trials), 4),
        "mean_mission_cost": round(fmean(x["mission_cost"] for x in trials), 2),
    }


def load_scenario(config_path: Optional[str]) -> Scenario:
    if not config_path:
        return Scenario()
    values = json.loads(Path(config_path).read_text(encoding="utf-8"))
    valid_keys = {field.name for field in fields(Scenario)}
    unknown_keys = set(values) - valid_keys
    if unknown_keys:
        raise ValueError(f"Unknown configuration fields: {', '.join(sorted(unknown_keys))}")
    return Scenario(**values)


def write_results(results: List[Dict[str, float]], output_dir: Path, scenario: Scenario) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "swarm_simulation_results.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    (output_dir / "swarm_simulation_results.json").write_text(
        json.dumps({"scenario": asdict(scenario), "results": results}, indent=2), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare swarm routing strategies with Monte Carlo trials.")
    parser.add_argument("--sizes", default="10,20,40,80", help="Comma-separated swarm sizes.")
    parser.add_argument("--runs", type=int, default=5000, help="Trials per strategy and swarm size.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for repeatable results.")
    parser.add_argument("--config", help="Optional JSON scenario file.")
    parser.add_argument("--output", default="swarm_monte_carlo/output", help="Directory for CSV and JSON results.")
    args = parser.parse_args()

    if args.runs < 1:
        raise ValueError("--runs must be at least 1")
    swarm_sizes = [int(value.strip()) for value in args.sizes.split(",")]
    if any(size < 1 for size in swarm_sizes):
        raise ValueError("Every swarm size must be at least 1")

    scenario = load_scenario(args.config)
    results = []
    for swarm_size in swarm_sizes:
        for strategy_index, strategy in enumerate(STRATEGIES):
            results.append(simulate(strategy, swarm_size, args.runs, scenario, args.seed + swarm_size * 100 + strategy_index))

    write_results(results, Path(args.output), scenario)
    print(f"{'Strategy':<22} {'Swarm':>7} {'Survivors':>12} {'Completion':>13} {'Coverage':>11} {'Cost':>18}")
    for result in results:
        print(
            f"{result['strategy']:<22} {result['swarm_size']:>7} "
            f"{result['mean_surviving_drones']:>12.2f} "
            f"{result['mission_completion_probability']:>12.1%} "
            f"{result['mean_target_coverage']:>10.1%} "
            f"${result['mean_mission_cost']:>17,.0f}"
        )


if __name__ == "__main__":
    main()
