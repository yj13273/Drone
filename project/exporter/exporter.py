"""
exporter.py
===========

Exports placement outputs:

    sensor.csv
    nfz.csv

Terrain CSVs are exported separately by:

    terrain_exporter.py

Input:
    list[PlacedSensor]
    list[NFZ polygons]

Output:
    outputs/sensor.csv
    outputs/nfz.csv
"""

from __future__ import annotations

import csv
import os


class Exporter:

    def __init__(
        self,
        export_config
    ):

        self.cfg = export_config

        os.makedirs(
            "outputs",
            exist_ok=True
        )

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def export(
        self,
        sensors,
        nfz_polygons
    ):

        self.export_sensors(
            sensors
        )

        self.export_nfz(
            nfz_polygons
        )

    # --------------------------------------------------
    # sensor.csv
    # --------------------------------------------------

    def export_sensors(
        self,
        sensors
    ):

        with open(
            self.cfg.sensor_csv,
            "w",
            newline=""
        ) as file:

            writer = csv.writer(
                file
            )

            writer.writerow([
                "id",
                "sensor_type",
                "label",
                "x",
                "y",
                "z",
                "class"
            ])

            for sensor in sensors:

                writer.writerow(
                    sensor.to_csv_row()
                )

        print(
            f"[EXPORT] {self.cfg.sensor_csv}"
        )

    # --------------------------------------------------
    # nfz.csv
    # --------------------------------------------------

    for cid, polygon in enumerate(
    nfz_polygons,
    start=1
    ):

        p1 = polygon[0]
        p2 = polygon[1]
        p3 = polygon[2]

        writer.writerow([

            cid,
            "NFZ",

            p1[0],
            p1[1],
            p1[2],

            p2[0],
            p2[1],
            p2[2],

            p3[0],
            p3[1],
            p3[2]
        ])