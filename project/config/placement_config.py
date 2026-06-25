from dataclasses import dataclass

@dataclass
class PlacementConfig:

    radar_separation: int = 8
    infrared_separation: int = 5
    acoustic_separation: int = 5
    visual_separation: int = 5

    coverage_weight: float = 0.5
    suitability_weight: float = 0.5

    allow_water: bool = False

    radar_marker = "^"
    infrared_marker = "s"
    acoustic_marker = "o"
    visual_marker = "D"