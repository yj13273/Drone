"""
terrain_generator.py
====================

Generates:

terrain_height.csv
terrain_type.csv

World Model
-----------
100 x 100 x 100

X,Y:
    0..99

Z:
    0..99

1 XY unit = 1 km
1 Z unit = 100 m

Outputs
--------
height_map:
    z coordinate values

terrain_map:
    terrain enum values

No placement logic.
No sensor logic.
No probability logic.
"""

from __future__ import annotations

import random

import noise
import numpy as np

from config.terrain_config import TerrainConfig
from terrain.terrain_constants import *


class TerrainGenerator:

    def __init__(
        self,
        cfg: TerrainConfig
    ):

        self.cfg = cfg

        self.seed = cfg.seed

        np.random.seed(self.seed)
        random.seed(self.seed)

        self.grid_size_x = cfg.grid_size_x
        self.grid_size_y = cfg.grid_size_y

        self.height_map = np.zeros(
            (
                self.grid_size_x,
                self.grid_size_y
            ),
            dtype=np.uint8
        )

        self.terrain_map = np.zeros(
            (
                self.grid_size_x,
                self.grid_size_y
            ),
            dtype=np.uint8
        )

        self.water_mask = np.zeros_like(
            self.height_map,
            dtype=bool
        )

        self.forest_mask = np.zeros_like(
            self.height_map,
            dtype=bool
        )

        self.high_ground_positions = []

    # --------------------------------------------------
    # Base Terrain
    # --------------------------------------------------

    def generate_base_heightmap(
        self,
        scale=40.0,
        octaves=6,
        persistence=0.5,
        lacunarity=2.0
    ):

        terrain = np.zeros(
            (
                self.grid_size_x,
                self.grid_size_y
            ),
            dtype=np.float32
        )

        for x in range(self.grid_size_x):
            for y in range(self.grid_size_y):

                terrain[x, y] = noise.pnoise2(
                    x / scale,
                    y / scale,
                    octaves=octaves,
                    persistence=persistence,
                    lacunarity=lacunarity,
                    repeatx=self.grid_size_x,
                    repeaty=self.grid_size_y,
                    base=self.seed
                )

        terrain -= terrain.min()
        terrain /= terrain.max()

        terrain *= 12.0

        self.height_map = terrain.astype(
            np.uint8
        )

    # --------------------------------------------------
    # Mountain Ranges
    # --------------------------------------------------

    def add_mountain_ranges(
        self,
        count
    ):

        for _ in range(count):

            start_x = random.randint(10, 90)
            start_y = random.randint(10, 90)

            length = random.randint(
                15,
                40
            )

            angle = random.uniform(
                0,
                2 * np.pi
            )

            for step in range(length):

                cx = int(
                    start_x +
                    step * np.cos(angle)
                )

                cy = int(
                    start_y +
                    step * np.sin(angle)
                )

                if (
                    cx < 0 or
                    cy < 0 or
                    cx >= self.grid_size_x or
                    cy >= self.grid_size_y
                ):
                    continue

                radius = random.randint(
                    3,
                    6
                )

                peak_height = random.randint(
                    self.cfg.mountain_height_min,
                    self.cfg.mountain_height_max
                )

                for x in range(
                    max(0, cx - radius),
                    min(
                        self.grid_size_x,
                        cx + radius
                    )
                ):
                    for y in range(
                        max(0, cy - radius),
                        min(
                            self.grid_size_y,
                            cy + radius
                        )
                    ):

                        dist = np.hypot(
                            x - cx,
                            y - cy
                        )

                        if dist > radius:
                            continue

                        gain = (
                            (1 - dist / radius)
                            * peak_height
                        )

                        self.height_map[x, y] += gain

        self.height_map = np.clip(
            self.height_map,
            0,
            self.cfg.grid_size_z - 1
        )

    # --------------------------------------------------
    # Water Blobs
    # --------------------------------------------------

    def add_water_clusters(
        self,
        count
    ):

        for _ in range(count):

            sx = random.randint(0, 99)
            sy = random.randint(0, 99)

            frontier = [(sx, sy)]

            target_size = random.randint(
                80,
                250
            )

            while frontier and target_size > 0:

                x, y = frontier.pop()

                if (
                    x < 0 or
                    y < 0 or
                    x >= self.grid_size_x or
                    y >= self.grid_size_y
                ):
                    continue

                if self.water_mask[x, y]:
                    continue

                self.water_mask[x, y] = True

                self.height_map[x, y] = 0

                target_size -= 1

                for dx, dy in [
                    (-1, 0),
                    (1, 0),
                    (0, -1),
                    (0, 1)
                ]:

                    if random.random() < 0.7:

                        frontier.append(
                            (
                                x + dx,
                                y + dy
                            )
                        )

    # --------------------------------------------------
    # Forest Blobs
    # --------------------------------------------------

    def add_forest_clusters(
        self,
        count
    ):

        for _ in range(count):

            sx = random.randint(0, 99)
            sy = random.randint(0, 99)

            frontier = [(sx, sy)]

            target_size = random.randint(
                120,
                350
            )

            while frontier and target_size > 0:

                x, y = frontier.pop()

                if (
                    x < 0 or
                    y < 0 or
                    x >= self.grid_size_x or
                    y >= self.grid_size_y
                ):
                    continue

                if self.water_mask[x, y]:
                    continue

                if self.forest_mask[x, y]:
                    continue

                self.forest_mask[x, y] = True

                target_size -= 1

                for dx, dy in [
                    (-1, 0),
                    (1, 0),
                    (0, -1),
                    (0, 1)
                ]:

                    if random.random() < 0.65:

                        frontier.append(
                            (
                                x + dx,
                                y + dy
                            )
                        )

    # --------------------------------------------------
    # Terrain Classification
    # --------------------------------------------------

    def classify_terrain(self):

        self.terrain_map.fill(
            PLAIN
        )

        for x in range(self.grid_size_x):
            for y in range(self.grid_size_y):

                z = self.height_map[x, y]

                if self.water_mask[x, y]:

                    self.terrain_map[x, y] = WATER

                elif self.forest_mask[x, y]:

                    self.terrain_map[x, y] = FOREST

                elif z >= 18:

                    self.terrain_map[x, y] = MOUNTAIN

                elif z >= 10:

                    self.terrain_map[x, y] = HILL

                else:

                    self.terrain_map[x, y] = PLAIN

        self.detect_valleys()

        self.find_high_ground()

    # --------------------------------------------------
    # Valley Detection
    # --------------------------------------------------

    def detect_valleys(self):

        for x in range(
            1,
            self.grid_size_x - 1
        ):
            for y in range(
                1,
                self.grid_size_y - 1
            ):

                if (
                    self.terrain_map[x, y]
                    == WATER
                ):
                    continue

                local = self.height_map[
                    x - 1:x + 2,
                    y - 1:y + 2
                ]

                center = self.height_map[
                    x,
                    y
                ]

                if (
                    center <= local.mean() - 3
                    and
                    center <= np.min(local) + 2
                ):

                    self.terrain_map[
                        x,
                        y
                    ] = VALLEY

    # --------------------------------------------------
    # Strategic Peaks
    # --------------------------------------------------

    def find_high_ground(self):

        peaks = []

        for x in range(
            2,
            self.grid_size_x - 2
        ):
            for y in range(
                2,
                self.grid_size_y - 2
            ):

                if (
                    self.terrain_map[x, y]
                    != MOUNTAIN
                ):
                    continue

                local = self.height_map[
                    x - 2:x + 3,
                    y - 2:y + 3
                ]

                if (
                    self.height_map[x, y]
                    == np.max(local)
                    and
                    self.height_map[x, y] >= 20
                ):

                    peaks.append(
                        (
                            x,
                            y,
                            self.height_map[x, y]
                        )
                    )

        peaks.sort(
            key=lambda p: p[2],
            reverse=True
        )

        selected = []

        min_distance = 8

        for px, py, h in peaks:

            valid = True

            for sx, sy in selected:

                if (
                    np.hypot(
                        px - sx,
                        py - sy
                    )
                    < min_distance
                ):
                    valid = False
                    break

            if valid:

                selected.append(
                    (
                        px,
                        py
                    )
                )

            if len(selected) >= 10:
                break

        self.high_ground_positions = selected

    # --------------------------------------------------
    # Full Generation
    # --------------------------------------------------

    def generate(self):

        self.generate_base_heightmap()

        self.add_mountain_ranges(
            self.cfg.num_mountain_ranges
        )

        self.add_water_clusters(
            self.cfg.num_water_clusters
        )

        self.add_forest_clusters(
            self.cfg.num_forest_clusters
        )

        self.classify_terrain()

        return (
            self.height_map,
            self.terrain_map
        )