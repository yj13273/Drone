"""
visualization.py
----------------
All matplotlib figure generation for the UAV sensor placement project.

v2.0 changes
~~~~~~~~~~~~
* Sensor → ThreatSensor throughout
* sensor_type → threat_type throughout
* Placement figure legend title updated to "Threat Type"
* Sensor positions read from x_cell / y_cell (replaces x / y)
* No visual redesign — all existing plots retained unchanged

Figures produced
~~~~~~~~~~~~~~~~
1. terrain_type.png          — categorical terrain-type map
2. elevation.png             — continuous elevation heatmap
3. strategic_importance.png  — importance surface
4. nfz_overlay.png           — elevation + NFZ mask
5. suitability_<type>.png    — one per threat type
6. sensor_placement.png      — final placement map with all sensor overlays

Design
~~~~~~
* Each figure is saved to config.OUTPUT_DIR.
* Functions are stateless — pass in data, get a saved file.
* Figure/axis creation is separated from data logic for testability.

FUTURE extension points
~~~~~~~~~~~~~~~~~~~~~~~
* Add viewshed / LOS coverage overlay to sensor_placement figure.
* Add radar range rings around radar sensors.
* Export interactive HTML via plotly (swap render backend).
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")                          # headless rendering
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
from pathlib import Path
from typing import Dict, List

import config
from sensor_types import ThreatSensor


# Discrete colour map for terrain types:
# water=blue, plain=lime-green, forest=dark-green, urban=grey, mountain=brown
_TERRAIN_COLOURS = ["#4A90D9", "#A8D5A2", "#2D6A4F", "#888888", "#8B5E3C"]
_TERRAIN_CMAP    = ListedColormap(_TERRAIN_COLOURS)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_all(terrain_layers:   Dict[str, np.ndarray],
             suitability_maps: Dict[str, np.ndarray],
             sensors:          List[ThreatSensor],
             output_dir:       Path = config.OUTPUT_DIR) -> None:
    """
    Render and save every figure.

    Parameters
    ----------
    terrain_layers   : {layer_name: 2-D array}
    suitability_maps : {threat_type: 2-D suitability array}
    sensors          : list of placed ThreatSensor objects
    output_dir       : destination folder (created if absent)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    _plot_terrain_type   (terrain_layers["terrain_type"],         output_dir)
    _plot_elevation      (terrain_layers["elevation"],            output_dir)
    _plot_strategic      (terrain_layers["strategic_importance"],  output_dir)
    _plot_nfz_overlay    (terrain_layers["elevation"],
                          terrain_layers["nfz"],                  output_dir)

    for threat_type, smap in suitability_maps.items():
        _plot_suitability(smap, threat_type, output_dir)

    _plot_sensor_placement(terrain_layers["elevation"], sensors, output_dir)

    print(f"[visualization] All figures saved to {output_dir}")


# ---------------------------------------------------------------------------
# Individual figure functions (private)
# ---------------------------------------------------------------------------

def _plot_terrain_type(tt: np.ndarray, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 6), dpi=config.FIGURE_DPI)
    ax.imshow(tt, cmap=_TERRAIN_CMAP, vmin=0,
              vmax=len(_TERRAIN_COLOURS) - 1, origin="lower")
    ax.set_title("Terrain Type", fontsize=14, fontweight="bold")
    ax.set_xlabel("Column (x)"); ax.set_ylabel("Row (y)")
    patches = [mpatches.Patch(color=_TERRAIN_COLOURS[i],
                               label=config.TERRAIN_TYPE_LABELS[i])
               for i in range(len(_TERRAIN_COLOURS))]
    ax.legend(handles=patches, loc="lower right", fontsize=8, framealpha=0.85)
    _save(fig, out / "terrain_type.png")


def _plot_elevation(elev: np.ndarray, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 6), dpi=config.FIGURE_DPI)
    im = ax.imshow(elev, cmap="terrain", origin="lower")
    plt.colorbar(im, ax=ax, label="Normalised Elevation")
    ax.set_title("Elevation Map", fontsize=14, fontweight="bold")
    ax.set_xlabel("Column (x)"); ax.set_ylabel("Row (y)")
    _save(fig, out / "elevation.png")


def _plot_strategic(si: np.ndarray, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 6), dpi=config.FIGURE_DPI)
    im = ax.imshow(si, cmap="hot", origin="lower")
    plt.colorbar(im, ax=ax, label="Strategic Importance (0–1)")
    ax.set_title("Strategic Importance Map", fontsize=14, fontweight="bold")
    ax.set_xlabel("Column (x)"); ax.set_ylabel("Row (y)")
    _save(fig, out / "strategic_importance.png")


def _plot_nfz_overlay(elev: np.ndarray, nfz: np.ndarray, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 6), dpi=config.FIGURE_DPI)
    im = ax.imshow(elev, cmap="terrain", origin="lower", alpha=0.8)
    nfz_overlay = np.ma.masked_where(nfz == 0, nfz)
    ax.imshow(nfz_overlay, cmap="Reds", origin="lower", alpha=0.6)
    plt.colorbar(im, ax=ax, label="Elevation (normalised)")
    red_patch = mpatches.Patch(color="red", alpha=0.6, label="No-Fly Zone")
    ax.legend(handles=[red_patch], loc="lower right", fontsize=8)
    ax.set_title("Elevation + No-Fly Zones", fontsize=14, fontweight="bold")
    ax.set_xlabel("Column (x)"); ax.set_ylabel("Row (y)")
    _save(fig, out / "nfz_overlay.png")


def _plot_suitability(smap: np.ndarray, threat_type: str, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 6), dpi=config.FIGURE_DPI)
    im = ax.imshow(smap, cmap="viridis", origin="lower", vmin=0, vmax=1)
    plt.colorbar(im, ax=ax, label="Suitability Score (0–1)")
    ax.set_title(f"Placement Suitability — {threat_type.capitalize()}",
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("Column (x)"); ax.set_ylabel("Row (y)")
    _save(fig, out / f"suitability_{threat_type}.png")


def _plot_sensor_placement(elev:    np.ndarray,
                            sensors: List[ThreatSensor],
                            out:     Path) -> None:
    """
    Final placement map: elevation background + ThreatSensor scatter overlay.

    Markers and colours follow config.SENSOR_DEFINITIONS, keyed by threat_type.
    Positions read from x_cell (column) and y_cell (row).
    """
    fig, ax = plt.subplots(figsize=(9, 8), dpi=config.FIGURE_DPI)
    im = ax.imshow(elev, cmap="terrain", origin="lower", alpha=0.85)
    plt.colorbar(im, ax=ax, label="Elevation (normalised)", shrink=0.75)

    legend_handles = []
    plotted_types  = set()

    for s in sensors:
        defn   = config.SENSOR_DEFINITIONS[s.threat_type]
        colour = defn["color"]
        marker = defn["marker"]

        # Use grid-coordinate fields: x_cell = column, y_cell = row
        ax.scatter(s.x_cell, s.y_cell,
                   c=colour, marker=marker,
                   s=config.SENSOR_MARKER_SIZE,
                   edgecolors="white", linewidths=0.8,
                   zorder=5)

        if s.threat_type not in plotted_types:
            legend_handles.append(
                mpatches.Patch(color=colour,
                               label=s.threat_type.capitalize())
            )
            plotted_types.add(s.threat_type)

    ax.legend(handles=legend_handles, loc="lower right",
              fontsize=9, framealpha=0.9, title="Threat Type")

    # Annotate sensor IDs at small font size
    for s in sensors:
        ax.text(s.x_cell + 0.8, s.y_cell + 0.8, str(s.id),
                fontsize=5, color="white", zorder=6)

    ax.set_title("Final Threat Sensor Placement", fontsize=15, fontweight="bold")
    ax.set_xlabel("Column (x)"); ax.set_ylabel("Row (y)")
    _save(fig, out / "sensor_placement.png")


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _save(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=config.FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"[visualization] Saved {path.name}")