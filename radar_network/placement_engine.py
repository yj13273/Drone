"""
placement_engine.py
-------------------
Core threat-sensor placement logic.

v2.0 changes
~~~~~~~~~~~~
* Sensor → ThreatSensor throughout
* sensor_type → threat_type throughout
* ThreatSensor now populated with x_cell/y_cell, x_m/y_m, elevation, metadata
* Uses config.CELL_SIZE_M for metric coordinate computation
* Placement method / version recorded in ThreatSensor.metadata

Pipeline per threat type
~~~~~~~~~~~~~~~~~~~~~~~~
1. Build a placement-suitability map by taking a weighted sum of terrain layers.
2. Mask out cells that violate hard constraints (NFZ, out-of-bounds).
3. Greedily select cells: pick highest score → enforce minimum separation →
   repeat until the required count is placed.
4. Return ThreatSensor objects for export and visualisation.

Architecture hook for future weight methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
`build_suitability_map(terrain, weights)` accepts any `weights` dict.
To plug in AHP, optimisation, or literature-derived weights, replace what
`_get_weights()` returns — no other changes needed.

FUTURE extension points
~~~~~~~~~~~~~~~~~~~~~~~
* MCLP (Maximum Coverage Location Problem) batch placement.
* LOS / viewshed constraint masking before greedy selection.
* Genetic algorithm replacing the greedy selector.
* Antenna orientation optimisation post-placement.
"""

import numpy as np
from typing import Dict, List, Tuple

import config
from terrain_loader import TerrainData
from sensor_types   import ThreatSensor, PlacementRequest

# Placement engine version — recorded in every ThreatSensor.metadata block.
_ENGINE_VERSION    = "2.0"
_PLACEMENT_METHOD  = "weighted_greedy"


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def place_all_sensors(terrain: TerrainData,
                      request: PlacementRequest) -> List[ThreatSensor]:
    """
    Place all requested threat sensors and return the full sensor list.

    Parameters
    ----------
    terrain : loaded TerrainData
    request : PlacementRequest with per-type counts
    """
    all_sensors: List[ThreatSensor] = []
    global_id_counter = 1

    nfz       = terrain.get_layer("nfz")
    elevation  = terrain.get_layer("elevation")

    for threat_type in config.SENSOR_DEFINITIONS:
        count = request.counts.get(threat_type, 0)
        if count == 0:
            continue

        weights     = _get_weights(threat_type)
        suitability = build_suitability_map(terrain, weights)

        # Per-layer raw scores — stored in placement_factors for debugging
        layer_scores = _compute_layer_scores(terrain, weights)

        min_sep    = config.SENSOR_DEFINITIONS[threat_type]["min_sep"]
        placements = _greedy_place(suitability, nfz, count, min_sep)

        for (row, col) in placements:
            factors = {layer: float(arr[row, col])
                       for layer, arr in layer_scores.items()}

            # Metric coordinates derived from cell indices + world convention
            x_m = col * config.CELL_SIZE_M
            y_m = row * config.CELL_SIZE_M

            sensor = ThreatSensor(
                id               = global_id_counter,
                threat_type      = threat_type,
                x_cell           = int(col),
                y_cell           = int(row),
                x_m              = float(x_m),
                y_m              = float(y_m),
                elevation        = float(elevation[row, col]),
                placement_score  = float(suitability[row, col]),
                placement_factors= factors,
                metadata         = {
                    "placement_method":          _PLACEMENT_METHOD,
                    "placement_engine_version":  _ENGINE_VERSION,
                    # FUTURE: coverage_radius, frequency_band,
                    #         sensor_power, orientation
                },
            )
            all_sensors.append(sensor)
            global_id_counter += 1

        print(f"[placement_engine] Placed {len(placements):2d} × {threat_type:<10s}"
              f"  (requested {count})")

    return all_sensors


def build_suitability_map(terrain: TerrainData,
                           weights: Dict[str, float]) -> np.ndarray:
    """
    Compute a normalised weighted-sum suitability map.

    Parameters
    ----------
    terrain : TerrainData
    weights : {layer_name: weight}  (need not sum to 1 — normalised internally)

    Returns
    -------
    2-D float32 array in [0, 1]

    FUTURE: add non-linear combination models (multiplicative, fuzzy logic).
    """
    cols, rows = terrain.grid_size
    score        = np.zeros((rows, cols), dtype=np.float32)
    total_weight = 0.0

    for layer_name, w in weights.items():
        layer         = _resolve_layer(terrain, layer_name)
        score        += w * layer
        total_weight += w

    if total_weight > 1e-9:
        score /= total_weight

    return _normalise(score)


# ---------------------------------------------------------------------------
# Greedy placement
# ---------------------------------------------------------------------------

def _greedy_place(suitability: np.ndarray,
                  nfz:         np.ndarray,
                  count:       int,
                  min_sep:     int) -> List[Tuple[int, int]]:
    """
    Select `count` cells by descending suitability, enforcing minimum
    separation distance and avoiding NFZ cells.

    Algorithm
    ---------
    1. Mask out NFZ cells.
    2. Flatten and sort indices by score (descending).
    3. Iterate: accept cell if it satisfies min_sep from already-placed cells.

    FUTURE: replace with MCLP / ILP / genetic algorithm for global optimum.
    """
    mask   = (nfz == 0).astype(bool)          # True = eligible
    masked = np.where(mask, suitability, -1.0)

    # Flat indices sorted highest → lowest
    flat_sorted      = np.argsort(masked.ravel())[::-1]
    rows_all, cols_all = np.unravel_index(flat_sorted, suitability.shape)

    placed:     List[Tuple[int, int]] = []
    placed_arr = np.empty((0, 2), dtype=int)   # shape (n, 2) for fast distance

    for r, c in zip(rows_all, cols_all):
        if masked[r, c] < 0:
            break   # remaining candidates are NFZ or exhausted

        if placed_arr.shape[0] > 0:
            dists = np.sqrt(((placed_arr[:, 0] - r)**2 +
                             (placed_arr[:, 1] - c)**2))
            if dists.min() < min_sep:
                continue

        placed.append((r, c))
        placed_arr = np.vstack([placed_arr, [[r, c]]])

        if len(placed) >= count:
            break

    if len(placed) < count:
        print(f"[placement_engine] WARNING: could only place {len(placed)} "
              f"(requested {count}) — relax min_sep or reduce count.")

    return placed


# ---------------------------------------------------------------------------
# Weight resolution
# ---------------------------------------------------------------------------

def _get_weights(threat_type: str) -> Dict[str, float]:
    """
    Return the weight dict for a threat type from config.

    FUTURE: This function is the hook for AHP / optimisation weight providers.
    Replace body with:
        return ahp_module.compute_weights(threat_type, pairwise_matrix)
    or:
        return weight_optimizer.load(threat_type)
    """
    return config.SENSOR_WEIGHTS.get(threat_type, {})


def _resolve_layer(terrain: TerrainData, layer_name: str) -> np.ndarray:
    """
    Map a weight-config layer name to an actual numpy array.

    Standard layers are read directly from TerrainData.
    Derived / synthetic layers are computed on demand:
      terrain_type_urban  — binary mask of urban cells
      terrain_type_forest — binary mask of forest cells
      distance_from_urban — normalised distance transform from urban zones

    FUTURE: Add "slope", "aspect", "radar_shadow", "los_count" here.
    """
    # --- Standard layers (direct lookup) ---
    if layer_name in terrain.layers:
        return terrain.get_layer(layer_name)

    # --- Derived layers from terrain_type ---
    tt = terrain.get_layer("terrain_type")

    if layer_name == "terrain_type_urban":
        return (tt == 3).astype(np.float32)

    if layer_name == "terrain_type_forest":
        return (tt == 2).astype(np.float32)

    if layer_name == "distance_from_urban":
        # Cells far from urban noise score higher for acoustic sensors
        from scipy.ndimage import distance_transform_edt
        urban_mask = (tt == 3)
        if urban_mask.any():
            dist = distance_transform_edt(~urban_mask).astype(np.float32)
        else:
            rows, cols = tt.shape
            dist = np.ones((rows, cols), dtype=np.float32)
        return _normalise(dist)

    # FUTURE: add "slope", "aspect", "radar_shadow", "los_count" here

    print(f"[placement_engine] WARNING: unknown layer '{layer_name}' — using zeros.")
    rows, cols = tt.shape
    return np.zeros((rows, cols), dtype=np.float32)


def _compute_layer_scores(terrain: TerrainData,
                           weights: Dict[str, float]) -> Dict[str, np.ndarray]:
    """Return per-layer raw (un-weighted) arrays for placement_factors logging."""
    return {name: _resolve_layer(terrain, name) for name in weights}


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _normalise(arr: np.ndarray) -> np.ndarray:
    lo, hi = arr.min(), arr.max()
    if hi - lo < 1e-9:
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)


# ---------------------------------------------------------------------------
# Suitability map getter (for visualisation)
# ---------------------------------------------------------------------------

def get_all_suitability_maps(terrain: TerrainData) -> Dict[str, np.ndarray]:
    """
    Return a dict of {threat_type: suitability_map} for all threat types.
    Used by visualization.py to render one subplot per type.
    """
    return {
        tt: build_suitability_map(terrain, _get_weights(tt))
        for tt in config.SENSOR_DEFINITIONS
    }