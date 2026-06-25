from dataclasses import dataclass

@dataclass
class ExportConfig:

    terrain_height_csv = "outputs/terrain_height.csv"
    terrain_type_csv = "outputs/terrain_type.csv"

    sensor_csv = "outputs/sensor.csv"
    nfz_csv = "outputs/nfz.csv"

    terrain_cost_csv = "outputs/terrain_cost.csv"