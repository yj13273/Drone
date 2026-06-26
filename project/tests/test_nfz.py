import numpy as np

from placement.nfz_generator import NFZGenerator
from placement.nfz import NFZLoader


def test_nfz_selects_four_polygons():
    nfzs = NFZGenerator.generate(seed=42, count=4)

    assert len(nfzs) == 4

    for poly in nfzs:
        assert len(poly) == 3

        for x, y, z in poly:
            assert 0 <= x < 100
            assert 0 <= y < 100
            assert 0 <= z < 100


def test_nfz_seed_reproducibility():
    nfz1 = NFZGenerator.generate(seed=42, count=4)
    nfz2 = NFZGenerator.generate(seed=42, count=4)

    assert nfz1 == nfz2


def test_nfz_mask_shape_empty_if_no_file_needed():
    mask = np.zeros((100, 100), dtype=np.uint8)

    assert NFZLoader.is_inside_nfz(10, 10, mask) is False or NFZLoader.is_inside_nfz(10, 10, mask) == 0