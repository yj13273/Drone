"""
terrain_generator.py
--------------------
Generates a synthetic multi-layer terrain and writes it to terrain.json.

Design goals
~~~~~~~~~~~~
* All randomness is seeded via config.TERRAIN_SEED for reproducibility.
* Each layer is a flat Python list-of-lists (JSON-serialisable).
* The JSON schema is designed so that a future terrain_loader.py can load
  real GIS data in the same format with zero changes to downstream modules.

Layers produced
~~~~~~~~~~~~~~~
  elevation            – Gaussian-smoothed noise, normalised 0-1.
  terrain_type         – Integer category grid (0=water … 4=mountain).
  strategic_importance – Sum-of-Gaussians importance surface, normalised 0-1.
  visibility_modifier  – Derived from elevation + terrain_type, normalised 0-1.
  nfz                  – Binary mask, 1 = No-Fly Zone.

FUTURE extension points
~~~~~~~~~~~~~~~~~~~~~~~
* Replace `_generate_elevation` with a real DEM reader (GeoTIFF / HDF5).
* Replace `_classify_terrain_type` with a land-use raster import.
* Add layers: slope, aspect, LOS_mask, radar_shadow, acoustic_attenuation.
"""

import json
import numpy as np
from pathlib import Path
from scipy.ndimage import gaussian_filter   # lightweight, no GIS dependency
from typing import Dict, List

import config


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_and_save(output_path: Path = config.TERRAIN_FILE) -> Dict:
    """
    Generate all terrain layers, build the JSON structure, and write to disk.

    Returns the terrain dict so callers can use it without re-reading the file.
    """
    rng = np.random.default_rng(config.TERRAIN_SEED)
    cols, rows = config.GRID_SIZE

    elevation            = _generate_elevation(rng, rows, cols)
    terrain_type         = _classify_terrain_type(elevation, rng, rows, cols)
    strategic_importance = _generate_strategic_importance(rows, cols)
    visibility_modifier  = _generate_visibility_modifier(elevation, terrain_type)
    nfz                  = _generate_nfz(rows, cols)

    terrain = {
        "metadata": {
            "grid_size":         list(config.GRID_SIZE),
            "cell_resolution":   config.CELL_RESOLUTION,
            "coordinate_system": config.COORDINATE_SYSTEM,
            "terrain_type_labels": config.TERRAIN_TYPE_LABELS,
            # FUTURE: add CRS, bounding_box, datum, projection when using real data
        },
        "layers": {
            "elevation":            elevation.tolist(),
            "terrain_type":         terrain_type.tolist(),
            "strategic_importance": strategic_importance.tolist(),
            "visibility_modifier":  visibility_modifier.tolist(),
            "nfz":                  nfz.tolist(),
        },
    }

    output_path.write_text(json.dumps(terrain, indent=2))
    print(f"[terrain_generator] Saved terrain to {output_path}")
    return terrain


# ---------------------------------------------------------------------------
# Layer generators (private)
# ---------------------------------------------------------------------------

def _generate_elevation(rng: np.random.Generator, rows: int, cols: int) -> np.ndarray:
    """
    Produce a plausible elevation map using Gaussian-smoothed random noise.

    A single octave of noise is smoothed heavily to mimic rolling terrain.
    Multiple Gaussian bumps are added to simulate mountain ranges.

    FUTURE: Replace with multi-octave Perlin noise or a real DEM.
    """
    # Base random field
    raw = rng.standard_normal((rows, cols))
    smooth = gaussian_filter(raw, sigma=config.ELEVATION_SIGMA)

    # Add a few prominent peaks
    for _ in range(4):
        cx, cy = rng.integers(10, cols - 10), rng.integers(10, rows - 10)
        sigma  = rng.uniform(5, 15)
        amp    = rng.uniform(0.5, 1.5)
        Y, X   = np.ogrid[:rows, :cols]
        bump   = amp * np.exp(-((X - cx)**2 + (Y - cy)**2) / (2 * sigma**2))
        smooth += bump

    return _normalise(smooth)


def _classify_terrain_type(elevation: np.ndarray,
                            rng: np.random.Generator,
                            rows: int, cols: int) -> np.ndarray:
    """
    Derive a terrain-type integer grid from elevation + random noise.

    Classes (matching config.TERRAIN_TYPE_LABELS):
      0 = water    (lowest elevations)
      1 = plain    (low-mid elevation)
      2 = forest   (mid elevation)
      3 = urban    (scattered low-elevation patches)
      4 = mountain (high elevation)

    FUTURE: Replace with a land-use raster import.
    """
    terrain = np.zeros((rows, cols), dtype=int)

    # Elevation thresholds
    terrain[elevation >= 0.75] = 4  # mountain
    terrain[(elevation >= 0.45) & (elevation < 0.75)] = 2  # forest
    terrain[(elevation >= 0.20) & (elevation < 0.45)] = 1  # plain
    terrain[elevation < 0.20] = 0   # water

    # Scatter urban patches near low-mid elevation zones
    noise = gaussian_filter(rng.standard_normal((rows, cols)), sigma=4)
    urban_mask = (noise > 1.1) & (elevation > 0.18) & (elevation < 0.55)
    terrain[urban_mask] = 3

    return terrain


def _generate_strategic_importance(rows: int, cols: int) -> np.ndarray:
    """
    Sum-of-Gaussians surface representing high-value targets.

    Zone parameters are defined in config.STRATEGIC_ZONES so they can be
    adjusted without touching this function.

    FUTURE: Replace with actual intelligence-layer overlay (e.g. OSM POI data).
    """
    importance = np.zeros((rows, cols))
    Y, X = np.ogrid[:rows, :cols]

    for (cx, cy, sigma, amp) in config.STRATEGIC_ZONES:
        importance += amp * np.exp(-((X - cx)**2 + (Y - cy)**2) / (2 * sigma**2))

    return _normalise(importance)


def _generate_visibility_modifier(elevation: np.ndarray,
                                   terrain_type: np.ndarray) -> np.ndarray:
    """
    Approximate visibility modifier: high elevation & open ground → high visibility.

    Simple heuristic for the prototype.  Replace with a true viewshed / LOS
    calculation in a future phase.

    FUTURE: compute_viewshed(elevation, observer_height) → 2-D bool array
    """
    # Visibility improves with elevation
    vis = elevation.copy()

    # Forests reduce visibility
    vis[terrain_type == 2] *= 0.5

    # Urban areas slightly reduce visibility (buildings cause scatter)
    vis[terrain_type == 3] *= 0.75

    # Water provides clear visibility (low relief)
    vis[terrain_type == 0] = np.clip(vis[terrain_type == 0] + 0.2, 0, 1)

    return _normalise(vis)


def _generate_nfz(rows: int, cols: int) -> np.ndarray:
    """
    Binary No-Fly Zone mask built from circular exclusion zones.

    Zone parameters come from config.NFZ_ZONES.

    FUTURE: Import NFZ polygons from airspace management system (GeoJSON / KML).
    """
    nfz = np.zeros((rows, cols), dtype=int)
    Y, X = np.ogrid[:rows, :cols]

    for (cx, cy, radius) in config.NFZ_ZONES:
        dist = np.sqrt((X - cx)**2 + (Y - cy)**2)
        nfz[dist <= radius] = 1

    return nfz


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _normalise(arr: np.ndarray) -> np.ndarray:
    """Min-max normalise to [0, 1]."""
    lo, hi = arr.min(), arr.max()
    if hi - lo < 1e-9:
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)