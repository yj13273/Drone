"""
sensor_types.py
---------------
Dataclasses that represent threat-sensor instances and placement requests.

v2.0 changes
~~~~~~~~~~~~
* Sensor  → ThreatSensor
* sensor_type → threat_type
* x/y → x_cell/y_cell  (grid coords) + x_m/y_m (metric coords)
* elevation field added for downstream LOS compatibility
* metadata block added (extensible) for placement method tracking

Keeping type definitions here means downstream modules — Threat Modeler,
Route Planner, exporter — can import them without pulling in heavy deps.

FUTURE extension points
~~~~~~~~~~~~~~~~~~~~~~~
* Add coverage_model field (callable) for sensor-specific footprint shapes.
* Add detection_curve (probability vs range) for threat modelling.
* Add power_consumption, maintenance_interval for logistics optimisation.
* Populate metadata.coverage_radius, frequency_band, sensor_power, orientation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import config


# ---------------------------------------------------------------------------
# Individual threat-sensor instance (placed on the grid)
# ---------------------------------------------------------------------------

@dataclass
class ThreatSensor:
    """
    A single placed threat-generating sensor.

    Fields
    ------
    id                : unique integer identifier
    threat_type       : one of "radar", "infrared", "acoustic", "visual"

    x_cell            : column index on the grid  (0 … GRID_WIDTH_CELLS-1)
    y_cell            : row index on the grid      (0 … GRID_HEIGHT_CELLS-1)

    x_m               : x_cell * CELL_SIZE_M  — metric easting  (metres)
    y_m               : y_cell * CELL_SIZE_M  — metric northing (metres)

    elevation         : normalised terrain elevation at placement cell (0-1)
                        Captured for downstream LOS / ray-marching calculations.
                        Not used operationally by the placement engine.

    placement_score   : overall suitability score at placement cell (0-1)
    placement_factors : per-layer contributions to the score (for debugging)

    metadata          : extensible dict — placement method, engine version, etc.
                        FUTURE: add coverage_radius, frequency_band,
                                sensor_power, orientation
    """
    id:                int
    threat_type:       str

    x_cell:            int
    y_cell:            int
    x_m:               float
    y_m:               float

    elevation:         float

    placement_score:   float
    placement_factors: Dict[str, float] = field(default_factory=dict)
    metadata:          Dict[str, Any]   = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Serialise to a JSON-compatible dict."""
        return {
            "id":          self.id,
            "threat_type": self.threat_type,

            "x_cell": self.x_cell,
            "y_cell": self.y_cell,
            "x_m":    round(self.x_m, 2),
            "y_m":    round(self.y_m, 2),

            "elevation": round(self.elevation, 4),

            "placement_score":   round(self.placement_score, 4),
            "placement_factors": {k: round(v, 4)
                                  for k, v in self.placement_factors.items()},
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Placement request: what the user asked for
# ---------------------------------------------------------------------------

@dataclass
class PlacementRequest:
    """
    A user-supplied request: how many threat sensors of each type to place.

    Fields
    ------
    counts : dict of threat_type → requested count
             e.g. {"radar": 8, "infrared": 4, "acoustic": 4, "visual": 4}
    """
    counts: Dict[str, int]

    @property
    def total(self) -> int:
        return sum(self.counts.values())

    def threat_types(self) -> List[str]:
        """Return list of threat types that have at least one sensor requested."""
        return [t for t, n in self.counts.items() if n > 0]