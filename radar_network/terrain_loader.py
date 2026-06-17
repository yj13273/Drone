"""
terrain_loader.py

Loads terrain.json (synthetic or real) and exposes typed numpy arrays.

Decoupling the loader from the generator means downstream modules never
need to know whether terrain came from a synthetic function or a GIS file.

Graceful degradation

If an optional layer is absent from the JSON, `get_layer` returns a
sensible default (zeros) and logs a warning.  This lets the placement
engine run even if the terrain team delivers an incomplete dataset.

FUTURE extension points

* Add `load_geotiff(path)` → calls GDAL, reprojects to grid, calls `load_dict`.
* Add `load_vector_layer(path, field)` → rasterise polygon attribute into grid.
* Add validation against a JSON schema (jsonschema library).
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple

import config



# Data class


class TerrainData:
    """
    Thin wrapper around the loaded terrain dict.

    Attributes
    
    grid_size   : (cols, rows)
    resolution  : metres per cell
    layers      : dict of layer_name → 2-D numpy array
    metadata    : raw metadata dict for downstream reference
    """

    def __init__(self, raw: Dict):
        self.metadata: Dict    = raw.get("metadata", {})
        self.grid_size: Tuple  = tuple(self.metadata.get("grid_size",
                                                          config.GRID_SIZE))
        self.resolution: int   = self.metadata.get("cell_resolution",
                                                    config.CELL_RESOLUTION)
        self._raw_layers: Dict = raw.get("layers", {})
        self.layers: Dict[str, np.ndarray] = {}
        self._load_layers()

 
    def _load_layers(self) -> None:
        """Convert every list-of-lists in JSON to a numpy float32 array."""
        for name, data in self._raw_layers.items():
            self.layers[name] = np.array(data, dtype=np.float32)

    
    def get_layer(self, name: str,
                  default: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Return a layer by name, with a graceful fallback.

        Parameters
        
        name    : layer key, e.g. "elevation"
        default : returned if layer is missing; defaults to zero grid.
        """
        if name in self.layers:
            return self.layers[name]

        rows, cols = int(self.grid_size[1]), int(self.grid_size[0])
        if default is None:
            default = np.zeros((rows, cols), dtype=np.float32)

        print(f"[terrain_loader] WARNING: layer '{name}' not found — "
              f"substituting zeros. Add it to terrain.json when available.")
        return default

  
    def available_layers(self):
        """Return a sorted list of all layer names present in the file."""
        return sorted(self.layers.keys())



# Public loader


def load(path: Path = config.TERRAIN_FILE) -> TerrainData:
    """
    Load terrain from a JSON file and return a TerrainData object.

    Parameters
    
    path : path to terrain.json (defaults to config.TERRAIN_FILE)
    """
    if not path.exists():
        raise FileNotFoundError(
            f"[terrain_loader] terrain file not found: {path}\n"
            "Run terrain_generator.generate_and_save() first."
        )

    raw = json.loads(path.read_text())
    td  = TerrainData(raw)
    print(f"[terrain_loader] Loaded terrain from {path}")
    print(f"  Grid size : {td.grid_size}")
    print(f"  Layers    : {td.available_layers()}")
    return td