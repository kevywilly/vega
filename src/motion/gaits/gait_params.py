from dataclasses import dataclass

@dataclass
class GaitParams:
    stride: int = 55
    clearance: int = 65
    step_size: int = 15
    turn_direction: int = 1
    is_reversed: bool = False
    hip_sway: int = 6
    pivot_ratio: float = 0.7