import os

from config.terrain_config import TerrainConfig
from config.sensor_config import SensorConfig
from config.placement_config import PlacementConfig
from config.export_config import ExportConfig

from terrain.terrain_generator import TerrainGenerator
from terrain.terrain_exporter import TerrainExporter

from placement.nfz_generator import NFZGenerator
from placement.layer_builder import LayerBuilder
from placement.placement_engine import PlacementEngine

from export.exporter import Exporter


def test_generate_real_outputs():
    terrain_cfg = TerrainConfig(seed=42)
    sensor_cfg = SensorConfig()
    placement_cfg = PlacementConfig()
    export_cfg = ExportConfig()

    tg = TerrainGenerator(terrain_cfg)
    height_map, terrain_map = tg.generate()

    TerrainExporter.export(
        height_map,
        terrain_map,
        output_dir="outputs"
    )

    nfz_polygons = NFZGenerator.generate(
        seed=terrain_cfg.seed,
        count=4
    )

    exporter = Exporter(export_cfg)

    exporter.export_nfz(nfz_polygons)

    lb = LayerBuilder(
        tg,
        nfz_file=export_cfg.nfz_csv
    )

    engine = PlacementEngine(
        tg,
        lb,
        placement_cfg
    )

    sensor_counts = {
        "radar": sensor_cfg.radar_count,
        "infrared": sensor_cfg.infrared_count,
        "visual": sensor_cfg.visual_count,
        "acoustic": sensor_cfg.acoustic_count,
    }

    sensors = engine.place(sensor_counts)

    exporter.export_sensors(sensors)

    assert os.path.exists("outputs/terrain_height.csv")
    assert os.path.exists("outputs/terrain_type.csv")
    assert os.path.exists("outputs/sensor.csv")
    assert os.path.exists("outputs/nfz.csv")