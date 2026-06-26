from config.terrain_config import TerrainConfig
from config.placement_config import PlacementConfig
from config.sensor_config import SensorConfig

from terrain.terrain_generator import TerrainGenerator
from terrain.terrain_constants import WATER

from placement.layer_builder import LayerBuilder
from placement.placement_engine import PlacementEngine


def test_placement_generates_requested_sensors_or_less():
    terrain_cfg = TerrainConfig(seed=42)
    placement_cfg = PlacementConfig()
    sensor_cfg = SensorConfig()

    tg = TerrainGenerator(terrain_cfg)
    tg.generate()

    lb = LayerBuilder(tg)

    engine = PlacementEngine(
        tg,
        lb,
        placement_cfg
    )

    counts = {
        "radar": sensor_cfg.radar_count,
        "infrared": sensor_cfg.infrared_count,
        "visual": sensor_cfg.visual_count,
        "acoustic": sensor_cfg.acoustic_count,
    }

    sensors = engine.place(counts)

    assert len(sensors) <= sum(counts.values())
    assert len(sensors) > 0


def test_no_sensor_on_water():
    terrain_cfg = TerrainConfig(seed=42)
    placement_cfg = PlacementConfig()

    tg = TerrainGenerator(terrain_cfg)
    tg.generate()

    lb = LayerBuilder(tg)

    engine = PlacementEngine(
        tg,
        lb,
        placement_cfg
    )

    sensors = engine.place({
        "radar": 8,
        "infrared": 8,
        "visual": 8,
        "acoustic": 8,
    })

    for sensor in sensors:
        assert tg.terrain_map[sensor.x, sensor.y] != WATER


def test_sensor_coordinates_are_valid():
    terrain_cfg = TerrainConfig(seed=42)
    placement_cfg = PlacementConfig()

    tg = TerrainGenerator(terrain_cfg)
    tg.generate()

    lb = LayerBuilder(tg)

    engine = PlacementEngine(
        tg,
        lb,
        placement_cfg
    )

    sensors = engine.place({
        "radar": 4,
        "infrared": 4,
        "visual": 4,
        "acoustic": 4,
    })

    for sensor in sensors:
        assert 0 <= sensor.x < 100
        assert 0 <= sensor.y < 100
        assert 0 <= sensor.z < 100
        assert 0 <= sensor.terrain_class <= 5