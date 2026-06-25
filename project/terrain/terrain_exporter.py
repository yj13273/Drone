import os
import numpy as np


class TerrainExporter:

    @staticmethod
    def export(
        height_map,
        terrain_map,
        output_dir="outputs"
    ):

        os.makedirs(
            output_dir,
            exist_ok=True
        )

        np.savetxt(
            f"{output_dir}/terrain_height.csv",
            height_map,
            fmt="%d",
            delimiter=","
        )

        np.savetxt(
            f"{output_dir}/terrain_type.csv",
            terrain_map,
            fmt="%d",
            delimiter=","
        )

        print(
            "[EXPORT] terrain_height.csv"
        )

        print(
            "[EXPORT] terrain_type.csv"
        )