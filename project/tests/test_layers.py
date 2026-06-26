import numpy as np

from config.terrain_config import TerrainConfig
from terrain.terrain_generator import TerrainGenerator
from placement.layer_builder import LayerBuilder


def test_layer_builder_outputs_correct_shapes():
    cfg = TerrainConfig(seed=42)
    tg = TerrainGenerator(cfg)
    tg.generate()

    lb = LayerBuilder(tg)

    assert lb.elevation_layer.shape == (100, 100)
    assert lb.visibility_layer.shape == (100, 100)
    assert lb.strategic_layer.shape == (100, 100)
    assert lb.nfz_mask.shape == (100, 100)

    assert "radar" in lb.suitability_maps
    assert "infrared" in lb.suitability_maps
    assert "visual" in lb.suitability_maps
    assert "acoustic" in lb.suitability_maps


def test_layers_are_normalized():
    cfg = TerrainConfig(seed=42)
    tg = TerrainGenerator(cfg)
    tg.generate()

    lb = LayerBuilder(tg)

    assert lb.elevation_layer.min() >= 0
    assert lb.elevation_layer.max() <= 1

    assert lb.visibility_layer.min() >= 0
    assert lb.visibility_layer.max() <= 1

    assert lb.strategic_layer.min() >= 0
    assert lb.strategic_layer.max() <= 1


def test_suitability_maps_valid_range():
    cfg = TerrainConfig(seed=42)
    tg = TerrainGenerator(cfg)
    tg.generate()

    lb = LayerBuilder(tg)

    for name, suit in lb.suitability_maps.items():
        assert suit.shape == (100, 100)
        assert suit.min() >= 0
        assert suit.max() <= 1