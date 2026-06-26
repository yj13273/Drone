"""
test.py
========

Full integration test for UAV Sensor Placement System
"""

from config.terrain_config import TerrainConfig
from config.placement_config import PlacementConfig
from config.export_config import ExportConfig
from config.sensor_config import SensorConfig

from terrain.terrain_generator import TerrainGenerator
from terrain.terrain_exporter import TerrainExporter

from placement.nfz_generator import NFZGenerator
from placement.layer_builder import LayerBuilder
from placement.placement_engine import PlacementEngine

from exporter import Exporter

from visualization.visualization_manager import VisualizationManager


def main():

    print("\n==============================")
    print(" UAV SENSOR PLACEMENT SYSTEM ")
    print("==============================\n")

    # ----------------------------------------
    # Config
    # ----------------------------------------

    terrain_cfg = TerrainConfig(
        seed=42
    )

    placement_cfg = PlacementConfig()

    export_cfg = ExportConfig()

    sensor_cfg = SensorConfig()

    # ----------------------------------------
    # Terrain Generation
    # ----------------------------------------

    print("[1/7] Generating Terrain...")

    tg = TerrainGenerator(
        terrain_cfg
    )

    tg.generate()

    print("Terrain Generated")

    # ----------------------------------------
    # Export Terrain
    # ----------------------------------------

    print("[2/7] Exporting Terrain CSVs...")

    TerrainExporter.export(
        tg.height_map,
        tg.terrain_map
    )

    # ----------------------------------------
    # NFZ Generation
    # ----------------------------------------

    print("[3/7] Generating NFZs...")

    nfz_polygons = NFZGenerator.generate(
        seed=terrain_cfg.seed,
        count=4
    )

    NFZGenerator.export_csv(
        nfz_polygons
    )

    print(
        f"Generated {len(nfz_polygons)} NFZ polygons"
    )

    # ----------------------------------------
    # Layer Building
    # ----------------------------------------

    print("[4/7] Building Layers...")

    lb = LayerBuilder(
        tg
    )

    print("Layers Built")

    # ----------------------------------------
    # Placement
    # ----------------------------------------

    print("[5/7] Placing Sensors...")

    engine = PlacementEngine(
        tg,
        lb,
        placement_cfg
    )

    sensors = engine.place({

        "radar":
            sensor_cfg.radar_count,

        "infrared":
            sensor_cfg.infrared_count,

        "acoustic":
            sensor_cfg.acoustic_count,

        "visual":
            sensor_cfg.visual_count
    })

    print(
        f"Placed {len(sensors)} sensors"
    )

    # ----------------------------------------
    # Export Placement
    # ----------------------------------------

    print("[6/7] Exporting CSVs...")

    exporter = Exporter(
        export_cfg
    )

    exporter.export(
        sensors,
        nfz_polygons
    )

    # ----------------------------------------
    # Visualization
    # ----------------------------------------

    print("[7/7] Generating Visualizations...")

    viz = VisualizationManager(
        tg,
        lb,
        sensors,
        nfz_polygons
    )

    viz.generate_all()

    print("\n==============================")
    print(" COMPLETE ")
    print("==============================")

    print(
        "\nOutputs generated:"
    )

    print(
        "outputs/terrain_height.csv"
    )

    print(
        "outputs/terrain_type.csv"
    )

    print(
        "outputs/sensor.csv"
    )

    print(
        "outputs/nfz.csv"
    )

    print(
        "outputs/*.png"
    )


if __name__ == "__main__":
    main()