from __future__ import annotations

import numpy as np

from placement.sensor_types import SENSOR_TYPES
from placement.placed_sensor import PlacedSensor
from placement.nfz import NFZLoader

from terrain.terrain_constants import WATER


class PlacementEngine:

    def __init__(
        self,
        terrain_generator,
        layer_builder,
        placement_config
    ):

        self.tg = terrain_generator
        self.lb = layer_builder
        self.cfg = placement_config

        self.height_map = terrain_generator.height_map
        self.terrain_map = terrain_generator.terrain_map

        self.nfz_mask = layer_builder.nfz_mask
        self.suitability_maps = layer_builder.suitability_maps

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def place(
        self,
        sensor_counts: dict
    ) -> list[PlacedSensor]:

        placed = []

        next_id = 1

        for sensor_def in SENSOR_TYPES:

            count = sensor_counts.get(
                sensor_def.name,
                0
            )

            suitability = self.suitability_maps[
                sensor_def.name
            ]

            sensor_list = self._place_sensor_type(
                sensor_def.name,
                sensor_def.label,
                count,
                suitability,
                placed,
                next_id
            )

            placed.extend(sensor_list)

            next_id += len(sensor_list)

        return placed

    # --------------------------------------------------
    # Per sensor placement
    # --------------------------------------------------

    def _place_sensor_type(
        self,
        sensor_type,
        label,
        count,
        suitability,
        existing_sensors,
        starting_id
    ):

        placed = []

        flat_indices = np.argsort(
            suitability.ravel()
        )[::-1]

        candidates = np.column_stack(
            np.unravel_index(
                flat_indices,
                suitability.shape
            )
        )

        sensor_id = starting_id

        for x, y in candidates:

            if len(placed) >= count:
                break

            if not self._valid_location(
                x,
                y,
                sensor_type,
                existing_sensors + placed
            ):
                continue

            sensor = PlacedSensor(
                sensor_id=sensor_id,
                sensor_type=sensor_type,
                label=f"{label}_{len(placed)+1}",
                x=int(x),
                y=int(y),
                z=int(
                    self.height_map[x, y]
                ),
                terrain_class=int(
                    self.terrain_map[x, y]
                ),
                suitability_score=float(
                    suitability[x, y]
                )
            )

            placed.append(sensor)

            sensor_id += 1

        return placed

    # --------------------------------------------------
    # Location validation
    # --------------------------------------------------

    def _valid_location(
        self,
        x,
        y,
        sensor_type,
        existing_sensors
    ):

        # bounds check

        if (
            x < 0 or
            y < 0 or
            x >= self.height_map.shape[0] or
            y >= self.height_map.shape[1]
        ):
            return False

        # water forbidden

        if self.terrain_map[x, y] == WATER:
            return False

        # NFZ forbidden

        if NFZLoader.is_inside_nfz(
            x,
            y,
            self.nfz_mask
        ):
            return False

        separation = self._get_separation(
            sensor_type
        )

        for sensor in existing_sensors:

            if sensor.sensor_type != sensor_type:
                continue

            dx = sensor.x - x
            dy = sensor.y - y

            dist = np.hypot(
                dx,
                dy
            )

            if dist < separation:
                return False

        return True

    # --------------------------------------------------
    # Separation lookup
    # --------------------------------------------------

    def _get_separation(
        self,
        sensor_type
    ):

        lookup = {

            "radar":
                self.cfg.radar_separation,

            "infrared":
                self.cfg.infrared_separation,

            "visual":
                self.cfg.visual_separation,

            "acoustic":
                self.cfg.acoustic_separation
        }

        return lookup.get(
            sensor_type,
            5
        )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    def summary(
        self,
        placed
    ):

        result = {}

        for sensor in placed:

            result.setdefault(
                sensor.sensor_type,
                0
            )

            result[
                sensor.sensor_type
            ] += 1

        return result
