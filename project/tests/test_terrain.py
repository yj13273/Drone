import numpy as np

from config.terrain_config import TerrainConfig
from terrain.terrain_generator import TerrainGenerator
from terrain.terrain_constants import WATER, PLAIN, FOREST, HILL, VALLEY, MOUNTAIN


def test_terrain_generator_initializes():
    cfg = TerrainConfig(seed=42)
    tg = TerrainGenerator(cfg)

    assert tg.height_map.shape == (100, 100)
    assert tg.terrain_map.shape == (100, 100)
    assert tg.seed == 42


def test_terrain_full_generation():
    cfg = TerrainConfig(seed=42)
    tg = TerrainGenerator(cfg)

    height_map, terrain_map = tg.generate()

    assert height_map.shape == (100, 100)
    assert terrain_map.shape == (100, 100)

    assert height_map.min() >= 0
    assert height_map.max() <= 99

    valid_types = {WATER, PLAIN, FOREST, HILL, VALLEY, MOUNTAIN}
    assert set(np.unique(terrain_map)).issubset(valid_types)


def test_water_cells_have_zero_height():
    cfg = TerrainConfig(seed=42)
    tg = TerrainGenerator(cfg)

    tg.generate()

    water_cells = tg.terrain_map == WATER

    if water_cells.any():
        assert np.all(tg.height_map[water_cells] == 0)


def test_seed_reproducibility():
    cfg1 = TerrainConfig(seed=42)
    cfg2 = TerrainConfig(seed=42)

    tg1 = TerrainGenerator(cfg1)
    tg2 = TerrainGenerator(cfg2)

    h1, t1 = tg1.generate()
    h2, t2 = tg2.generate()

    assert np.array_equal(h1, h2)
    assert np.array_equal(t1, t2)