import csv

from config.export_config import ExportConfig
from placement.placed_sensor import PlacedSensor
from export.exporter import Exporter

def test_sensor_csv_export(tmp_path):
    cfg = ExportConfig()
    cfg.sensor_csv = str(tmp_path / "sensor.csv")
    cfg.nfz_csv = str(tmp_path / "nfz.csv")

    sensors = [
        PlacedSensor(
            sensor_id=1,
            sensor_type="radar",
            label="Radar_1",
            x=10,
            y=20,
            z=5,
            terrain_class=3,
            suitability_score=0.9
        )
    ]

    nfz_polygons = [
        [(1, 1, 0), (10, 1, 0), (5, 10, 0)]
    ]

    exporter = Exporter(cfg)
    exporter.export(sensors, nfz_polygons)

    with open(cfg.sensor_csv, newline="") as f:
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

    assert rows[1] == [
        "1",
        "radar",
        "Radar_1",
        "10",
        "20",
        "5",
        "3"
    ]


def test_nfz_csv_export(tmp_path):
    cfg = ExportConfig()
    cfg.sensor_csv = str(tmp_path / "sensor.csv")
    cfg.nfz_csv = str(tmp_path / "nfz.csv")

    sensors = []

    nfz_polygons = [
        [(1, 1, 0), (10, 1, 0), (5, 10, 0)]
    ]

    exporter = Exporter(cfg)
    exporter.export(sensors, nfz_polygons)

    with open(cfg.nfz_csv, newline="") as f:
        rows = list(csv.reader(f))

    assert rows[0] == [
        "Cid",
        "type",
        "x1", "y1", "z1",
        "x2", "y2", "z2",
        "x3", "y3", "z3"
    ]

    assert rows[1] == [
        "1",
        "NFZ",
        "1", "1", "0",
        "10", "1", "0",
        "5", "10", "0"
    ]