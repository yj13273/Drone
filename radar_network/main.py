"""
main.py
-------
Entry point for Phase 1A of the UAV Threat-Aware Route Planning project.
Sensor Placement Module — v2.0

Run
---
    python main.py

Pipeline
--------
1. Generate synthetic terrain and write terrain.json          (terrain_generator)
2. Prompt user for threat-sensor counts                       (this file)
3. Load terrain                                               (terrain_loader)
4. Compute suitability maps and place threat sensors          (placement_engine)
5. Render and save all visualisation figures                  (visualization)
6. Export sensor_map.json                                     (exporter)

v2.0 changes
~~~~~~~~~~~~
* Sensor → ThreatSensor throughout
* sensor_type → threat_type in prompts and print statements
* prompt function renamed _prompt_threat_sensor_counts
* PlacementRequest.sensor_types() → .threat_types()

Design note
-----------
This file contains only orchestration logic.  All business logic lives in
the imported modules so each can be tested and replaced independently.
"""

import sys
from pathlib import Path

# Ensure the project root is on the import path regardless of CWD
sys.path.insert(0, str(Path(__file__).parent))

import config
import terrain_generator
import terrain_loader
import placement_engine
import visualization
import exporter
from sensor_types import PlacementRequest


# ---------------------------------------------------------------------------
# User input helper
# ---------------------------------------------------------------------------

def _prompt_threat_sensor_counts() -> PlacementRequest:
    """
    Interactively ask the user for a total threat-sensor count and per-type
    breakdown.  The last type is auto-filled to prevent rounding errors.
    """
    threat_types = list(config.SENSOR_DEFINITIONS.keys())

    print("\n" + "=" * 55)
    print("  UAV Threat-Aware Route Planning — Phase 1A  v2.0")
    print("  Sensor Placement Module")
    print("=" * 55)

    # --- Total ---
    while True:
        try:
            total = int(input("\nEnter total number of threat sensors to place: "))
            if total > 0:
                break
            print("  Total must be a positive integer.")
        except ValueError:
            print("  Please enter a valid integer.")

    # --- Per-type counts ---
    print(f"\nDistribute {total} sensors across threat types.")
    print(f"Threat types available: {', '.join(threat_types)}")
    print("(Enter 0 for a type you do not want to place.)\n")

    counts: dict[str, int] = {}
    remaining = total

    for i, tt in enumerate(threat_types):
        while True:
            try:
                if i == len(threat_types) - 1:
                    # Auto-fill last type to absorb any remainder
                    print(f"  {tt.capitalize():12s}: auto-set to {remaining}")
                    counts[tt] = remaining
                    break

                val = int(input(f"  {tt.capitalize():12s}: "))
                if val < 0:
                    print("  Cannot be negative.")
                    continue
                if val > remaining:
                    print(f"  Only {remaining} sensors remain — enter ≤ {remaining}.")
                    continue

                counts[tt] = val
                remaining -= val
                break
            except ValueError:
                print("  Please enter a valid integer.")

    print(f"\nThreat sensor breakdown: {counts}")
    print(f"Total: {sum(counts.values())}")

    return PlacementRequest(counts=counts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Generate terrain ─────────────────────────────────────────
    print("\n[main] Generating synthetic terrain …")
    terrain_generator.generate_and_save(config.TERRAIN_FILE)

    # ── Step 2: User input ───────────────────────────────────────────────
    request = _prompt_threat_sensor_counts()

    # ── Step 3: Load terrain ─────────────────────────────────────────────
    print("\n[main] Loading terrain …")
    terrain = terrain_loader.load(config.TERRAIN_FILE)

    # ── Step 4: Placement ────────────────────────────────────────────────
    print("\n[main] Computing suitability maps and placing threat sensors …")
    sensors          = placement_engine.place_all_sensors(terrain, request)
    suitability_maps = placement_engine.get_all_suitability_maps(terrain)

    # ── Step 5: Visualisation ────────────────────────────────────────────
    print("\n[main] Rendering figures …")
    visualization.save_all(
        terrain_layers   = terrain.layers,   # Dict[str, np.ndarray]
        suitability_maps = suitability_maps,
        sensors          = sensors,
        output_dir       = config.OUTPUT_DIR,
    )

    # ── Step 6: Export ───────────────────────────────────────────────────
    print("\n[main] Exporting sensor map …")
    exporter.save_sensor_map(sensors, config.SENSOR_FILE)

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print("  Run complete.")
    print(f"  Terrain   → {config.TERRAIN_FILE}")
    print(f"  Sensors   → {config.SENSOR_FILE}")
    print(f"  Figures   → {config.OUTPUT_DIR}/")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()