from terrain.terrain_generator import TerrainGenerator
from terrain.terrain_exporter import TerrainExporter

from placement.layer_builder import LayerBuilder
from placement.placement_engine import PlacementEngine
from placement.nfz_generator import NFZGenerator

from config.terrain_config import TerrainConfig
from config.sensor_config import SensorConfig
from config.placement_config import PlacementConfig

from exporter import Exporter

from visualization.visualization_manager import (
    VisualizationManager
)

import random


def main():

    print("\n==============================")
    print(" UAV Sensor Placement System ")
    print("==============================\n")

    # ----------------------------------
    # Configs
    # ----------------------------------

    terrain_cfg = TerrainConfig()

    sensor_cfg = SensorConfig()

    placement_cfg = PlacementConfig()

    # ----------------------------------
    # Seed
    # ----------------------------------

    seed = terrain_cfg.seed

    if seed is None:

        seed = random.randint(
            0,
            100000
        )

    print(f"[INFO] Seed = {seed}")

    # ----------------------------------
    # Terrain Generation
    # ----------------------------------

    print("\n[1] Generating Terrain")

    tg = TerrainGenerator(
        seed=seed
    )

    height_map, terrain_map = (
        tg.generate()
    )

    print(
        f"Terrain Generated "
        f"({height_map.shape[0]}x{height_map.shape[1]})"
    )


    #NFZ selection

    selected_nfzs = NFZGenerator.generate(
    seed=seed,
    count=4
    )

    exporter.export(
    sensors=placed_sensors,
    nfz_polygons=nfz_polygons
    )

    # ----------------------------------
    # Export Terrain
    # ----------------------------------

    print("\n[2] Exporting Terrain CSVs")

    TerrainExporter.export(
        height_map,
        terrain_map
    )

    # ----------------------------------
    # Layer Builder
    # ----------------------------------

    print("\n[3] Building Layers")

    lb = LayerBuilder(
        tg
    )

    print(
        "Layers Generated"
    )

    # ----------------------------------
    # Sensor Counts
    # ----------------------------------

    sensor_counts = {

        "radar":
            sensor_cfg.radar_count,

        "infrared":
            sensor_cfg.infrared_count,

        "visual":
            sensor_cfg.visual_count,

        "acoustic":
            sensor_cfg.acoustic_count
    }

    print(
        "\nSensor Counts:"
    )

    for key, value in sensor_counts.items():

        print(
            f"  {key:<10} : {value}"
        )

    # ----------------------------------
    # Placement
    # ----------------------------------

    print(
        "\n[4] Running Placement Engine"
    )

    engine = PlacementEngine(
        tg,
        lb,
        placement_cfg
    )

    placed_sensors = engine.place(
        sensor_counts
    )

    print(
        f"{len(placed_sensors)} sensors placed"
    )

    # ----------------------------------
    # Export Sensors
    # ----------------------------------

    print(
        "\n[5] Exporting Sensors"
    )

    exporter = Exporter()

    exporter.export_sensors(
        placed_sensors
    )

    # ----------------------------------
    # Visualization
    # ----------------------------------

    print(
        "\n[6] Generating Figures"
    )

    viz = VisualizationManager()

    # Terrain

    fig = viz.terrain(
        terrain_map
    )

    viz.save(
        fig,
        "terrain.png"
    )

    # Sensors

    fig = viz.sensors(
        terrain_map,
        placed_sensors
    )

    viz.save(
        fig,
        "sensors.png"
    )

    # Suitability

    fig = viz.suitability(
        lb.suitability_maps
    )

    viz.save(
        fig,
        "suitability.png"
    )

    # Layers

    fig = viz.layers(
        lb.elevation_layer,
        lb.visibility_layer,
        lb.strategic_layer,
        lb.nfz_mask
    )

    viz.save(
        fig,
        "layers.png"
    )

    # Terrain 3D

    fig = viz.terrain_3d(
        height_map
    )

    viz.save(
        fig,
        "terrain_3d.png"
    )

    print(
        "\nFigures Saved"
    )

    # ----------------------------------
    # Summary
    # ----------------------------------

    print("\n==============================")
    print(" RUN COMPLETE ")
    print("==============================")

    print(
        f"Seed: {seed}"
    )

    print(
        f"Sensors Placed: "
        f"{len(placed_sensors)}"
    )

    print(
        "Outputs:"
    )

    print(
        "  terrain_height.csv"
    )

    print(
        "  terrain_type.csv"
    )

    print(
        "  sensor.csv"
    )

    print(
        "  terrain.png"
    )

    print(
        "  sensors.png"
    )

    print(
        "  suitability.png"
    )

    print(
        "  layers.png"
    )

    print(
        "  terrain_3d.png"
    )

    print()


if __name__ == "__main__":

    main()