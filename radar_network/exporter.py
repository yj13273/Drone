"""
exporter.py
-----------
Serialises the placed ThreatSensor list to sensor_map.json.

v2.0 changes
~~~~~~~~~~~~
* Sensor → ThreatSensor throughout
* sensor_type → threat_type in sensor counts
* Full metadata block added:
    - placement_engine_version, placement_method
    - terrain_source, cell_size_m
    - grid_size, world_size_m
    - coordinate_system, coordinate_convention
    - los_compatible, elevation_provided
* sensor_counts keyed by threat_type

Kept as a separate module so the export format can evolve independently
of the placement engine and visualisation layers.

FUTURE extension points
~~~~~~~~~~~~~~~~~~~~~~~
* Export to GeoJSON (with real coordinates after CRS is added).
* Export to KML for Google Earth overlay.
* Export coverage raster alongside sensor locations.
* Stream to a REST API endpoint.
* terrain_source: swap "synthetic" for "geotiff" / "srtm" / "lidar".
"""

import json
from pathlib import Path
from typing import List

import config
from sensor_types import ThreatSensor

# Matches value recorded inside each ThreatSensor.metadata block.
_ENGINE_VERSION   = "2.0"
_PLACEMENT_METHOD = "weighted_greedy"
_TERRAIN_SOURCE   = "synthetic"  # FUTURE: "geotiff", "srtm", "lidar", "gis_import"


def save_sensor_map(sensors: List[ThreatSensor],
                    output_path: Path = config.SENSOR_FILE) -> None:
    """
    Write ThreatSensor list to sensor_map.json.

    Parameters
    ----------
    sensors     : list of placed ThreatSensor objects
    output_path : destination file (defaults to config.SENSOR_FILE)
    """
    sensor_map = {
        "metadata": {
            # ── Engine provenance ─────────────────────────────────────────
            "placement_engine_version": _ENGINE_VERSION,
            "placement_method":         _PLACEMENT_METHOD,
            "terrain_source":           _TERRAIN_SOURCE,

            # ── World geometry ────────────────────────────────────────────
            "cell_size_m":  config.CELL_SIZE_M,
            "grid_size":    list(config.GRID_SIZE),           # [cols, rows]
            "world_size_m": [config.WORLD_WIDTH_M,
                             config.WORLD_HEIGHT_M],          # [10000, 10000]

            # ── Coordinate convention ─────────────────────────────────────
            # Explicit so downstream teams cannot misinterpret orientation.
            "coordinate_system": config.COORDINATE_SYSTEM,
            "coordinate_convention": {
                "origin":    "bottom_left",
                "x_axis":    "east",
                "y_axis":    "north",
                "cell_size_m": config.CELL_SIZE_M,
            },

            # ── LOS / downstream compatibility flags ──────────────────────
            "los_compatible":    True,   # elevation data present per sensor
            "elevation_provided": True,  # ThreatSensor.elevation is populated

            # ── Sensor counts ─────────────────────────────────────────────
            "total_sensors": len(sensors),
            "sensor_counts": {
                tt: sum(1 for s in sensors if s.threat_type == tt)
                for tt in config.SENSOR_DEFINITIONS
            },

            # FUTURE: add CRS, bounding_box when georeferencing is implemented
        },
        "sensors": [s.to_dict() for s in sensors],
    }

    output_path.write_text(json.dumps(sensor_map, indent=2))
    print(f"[exporter] Saved {len(sensors)} threat sensors to {output_path}")