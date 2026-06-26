import csv
import os
import numpy as np

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


def test_full_python_pipeline(tmp_path):
    # -----------------------------
    # Config
    # -----------------------------

    terrain_cfg = TerrainConfig(seed=42)

    sensor_cfg = SensorConfig(
        radar_count=4,
        infrared_count=4,
        acoustic_count=4,
        visual_count=4
    )

    placement_cfg = PlacementConfig()

    export_cfg = ExportConfig()
    export_cfg.terrain_height_csv = str(tmp_path / "terrain_height.csv")
    export_cfg.terrain_type_csv = str(tmp_path / "terrain_type.csv")
    export_cfg.sensor_csv = str(tmp_path / "sensor.csv")
    export_cfg.nfz_csv = str(tmp_path / "nfz.csv")

    # -----------------------------
    # Terrain generation
    # -----------------------------

    tg = TerrainGenerator(terrain_cfg)

    height_map, terrain_map = tg.generate()

    assert height_map.shape == (100, 100)
    assert terrain_map.shape == (100, 100)

    # -----------------------------
    # Terrain export
    # -----------------------------

    TerrainExporter.export(
        height_map,
        terrain_map,
        output_dir=str(tmp_path)
    )

    assert os.path.exists(export_cfg.terrain_height_csv)
    assert os.path.exists(export_cfg.terrain_type_csv)

    # -----------------------------
    # NFZ generation + export
    # -----------------------------

    nfz_polygons = NFZGenerator.generate(
        seed=terrain_cfg.seed,
        count=4
    )

    exporter = Exporter(export_cfg)

    exporter.export_nfz(
        nfz_polygons
    )

    assert os.path.exists(export_cfg.nfz_csv)

    # -----------------------------
    # IMPORTANT:
    # LayerBuilder currently reads outputs/nfz.csv by default.
    # So for this test, either:
    # 1. Update LayerBuilder to accept nfz_file, OR
    # 2. Copy test nfz.csv to outputs/nfz.csv.
    #
    # Recommended long-term fix:
    # LayerBuilder(tg, nfz_file=export_cfg.nfz_csv)
    # -----------------------------

    lb = LayerBuilder(
        tg,
        nfz_file=export_cfg.nfz_csv
    )

    assert lb.elevation_layer.shape == (100, 100)
    assert lb.visibility_layer.shape == (100, 100)
    assert lb.strategic_layer.shape == (100, 100)
    assert lb.nfz_mask.shape == (100, 100)

    # -----------------------------
    # Placement
    # -----------------------------

    engine = PlacementEngine(
        tg,
        lb,
        placement_cfg
    )

    sensor_counts = {
        "radar": sensor_cfg.radar_count,
        "infrared": sensor_cfg.infrared_count,
        "acoustic": sensor_cfg.acoustic_count,
        "visual": sensor_cfg.visual_count,
    }

    placed_sensors = engine.place(
        sensor_counts
    )

    assert len(placed_sensors) > 0
    assert len(placed_sensors) <= sum(sensor_counts.values())

    # -----------------------------
    # Sensor export
    # -----------------------------

    exporter.export_sensors(
        placed_sensors
    )

    assert os.path.exists(export_cfg.sensor_csv)

    # -----------------------------
    # Validate terrain CSV shape
    # -----------------------------

    loaded_height = np.loadtxt(
        export_cfg.terrain_height_csv,
        delimiter=",",
        dtype=int
    )

    loaded_type = np.loadtxt(
        export_cfg.terrain_type_csv,
        delimiter=",",
        dtype=int
    )

    assert loaded_height.shape == (100, 100)
    assert loaded_type.shape == (100, 100)

    # -----------------------------
    # Validate sensor.csv
    # -----------------------------

    with open(export_cfg.sensor_csv, newline="") as f:
        rows = list(csv.reader(f))

    assert rows[0] == [
        "id",
        "sensor_type",
        "label",
        "x",
        "y",
        "z",
        "class"
    ]

    assert len(rows) == len(placed_sensors) + 1

    # -----------------------------
    # Validate nfz.csv
    # -----------------------------

    with open(export_cfg.nfz_csv, newline="") as f:
        nfz_rows = list(csv.reader(f))

    assert nfz_rows[0] == [
        "Cid",
        "type",
        "x1",
        "y1",
        "z1",
        "x2",
        "y2",
        "z2",
        "x3",
        "y3",
        "z3"
    ]

    assert len(nfz_rows) == 5