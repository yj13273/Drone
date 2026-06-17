"""
config.py
---------
Central configuration for the UAV Threat-Aware Route Planning project.

All parameters that might change between experiments or deployments live here.
No magic numbers should exist in other modules — they should always trace back
to this file or to runtime user input.

Future extension points are marked with # FUTURE: comments.

World / grid convention (v2.0)
------------------------------
  Origin   : bottom-left corner of the grid
  X axis   : east  (column index increases eastward)
  Y axis   : north (row index increases northward)
  Cell size : CELL_SIZE_M metres per side

All downstream modules (Threat Modeling, Route Planning, LOS) must
use the same convention.  Do not assume a different origin or axis direction.
"""

from pathlib import Path
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Directory layout
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR   = PROJECT_ROOT / "outputs"
TERRAIN_FILE = PROJECT_ROOT / "terrain.json"
SENSOR_FILE  = PROJECT_ROOT / "sensor_map.json"

# ---------------------------------------------------------------------------
# Grid / world parameters
# ---------------------------------------------------------------------------
# Canonical world-convention constants — shared with Threat Modeling team.
CELL_SIZE_M: int        = 100          # metres per cell (one side)

GRID_WIDTH_CELLS: int   = 100          # number of columns
GRID_HEIGHT_CELLS: int  = 100          # number of rows

WORLD_WIDTH_M: int      = GRID_WIDTH_CELLS  * CELL_SIZE_M   # 10 000 m = 10 km
WORLD_HEIGHT_M: int     = GRID_HEIGHT_CELLS * CELL_SIZE_M   # 10 000 m = 10 km

# Legacy aliases kept for backward compatibility with terrain_generator.py
# and terrain_loader.py which use GRID_SIZE / CELL_RESOLUTION.
GRID_SIZE: Tuple[int, int] = (GRID_WIDTH_CELLS, GRID_HEIGHT_CELLS)  # (cols, rows)
CELL_RESOLUTION: int       = CELL_SIZE_M
COORDINATE_SYSTEM: str     = "local_grid"

# ---------------------------------------------------------------------------
# Terrain generation — synthetic noise parameters
# ---------------------------------------------------------------------------
TERRAIN_SEED: int = 42          # reproducible runs; change for variety

# Elevation smoothing: larger sigma → smoother hills
ELEVATION_SIGMA: float = 12.0

# Strategic-importance Gaussians: list of (cx, cy, sigma, amplitude) tuples
STRATEGIC_ZONES: List[Tuple[int, int, float, float]] = [
    (25, 25, 8,  1.0),   # city / military HQ
    (70, 60, 6,  0.9),   # industrial complex
    (50, 80, 5,  0.85),  # air base
    (85, 20, 7,  0.75),  # coastal installation
]

# No-Fly Zones: list of (cx, cy, radius_cells) tuples
NFZ_ZONES: List[Tuple[int, int, int]] = [
    (50, 50, 6),
    (15, 85, 5),
    (80, 35, 4),
]

# Terrain-type class labels (integer → name)
TERRAIN_TYPE_LABELS: Dict[int, str] = {
    0: "water",
    1: "plain",
    2: "forest",
    3: "urban",
    4: "mountain",
}

# ---------------------------------------------------------------------------
# Threat-sensor type definitions
# ---------------------------------------------------------------------------
# Keyed by threat_type string — the canonical term used throughout v2.
#
# Each entry carries:
#   - marker  : matplotlib marker code
#   - color   : matplotlib colour string
#   - min_sep : minimum cell separation for same-type sensors (greedy placement)
#
# FUTURE: add range_cells, detection_probability_model, sensor_fusion_weights,
#         frequency_band, orientation_deg
SENSOR_DEFINITIONS: Dict[str, Dict] = {
    "radar": {
        "marker": "^",        # triangle-up
        "color":  "red",
        "min_sep": 8,
    },
    "infrared": {
        "marker": "s",        # square
        "color":  "blue",
        "min_sep": 5,
    },
    "acoustic": {
        "marker": "o",        # circle
        "color":  "green",
        "min_sep": 5,
    },
    "visual": {
        "marker": "D",        # diamond
        "color":  "gold",
        "min_sep": 5,
    },
}

# ---------------------------------------------------------------------------
# Placement-suitability weight configurations
# ---------------------------------------------------------------------------
# Structure:  threat_type → { layer_name: weight, ... }
#
# Weights within each threat_type are normalised to sum = 1 inside
# placement_engine.py, so only relative magnitudes matter here.
#
# FUTURE extension points
# -----------------------
# Replace these hardcoded dicts with outputs from any of:
#   • AHP (Analytic Hierarchy Process) matrices
#   • Literature-derived weight tables
#   • Genetic algorithm / optimisation calibration
#   • Bayesian weight estimation
#
# The placement engine accepts any dict of {layer: weight} — swap freely.
SENSOR_WEIGHTS: Dict[str, Dict[str, float]] = {
    "radar": {
        "elevation":            0.40,
        "visibility_modifier":  0.35,
        "strategic_importance": 0.25,
    },
    "infrared": {
        "strategic_importance": 0.50,
        "terrain_type_urban":   0.30,   # proximity to urban areas
        "elevation":            0.20,
    },
    "acoustic": {
        "terrain_type_forest":  0.40,   # forests dampen acoustic scatter
        "distance_from_urban":  0.35,   # quieter = better baseline
        "strategic_importance": 0.25,
    },
    "visual": {
        "visibility_modifier":  0.55,
        "strategic_importance": 0.30,
        "elevation":            0.15,
    },
}

# ---------------------------------------------------------------------------
# Visualisation settings
# ---------------------------------------------------------------------------
FIGURE_DPI: int = 120
SENSOR_MARKER_SIZE: int = 100   # scatter plot s= parameter