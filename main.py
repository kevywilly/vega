from math import sin, cos
from lx16a import *
import time
import numpy as np

LX16A.initialize("/dev/ttyUSB0", 0.1)

def map(x, in_min, in_max, out_min, out_max) -> int:
  return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min);

def clip(v) -> int:
    return 0 if v < 0 else 240 if v > 240 else v

def signed_to_angle(angle: int) -> int:
    return map(angle, 0-240/2, 240/2, 0, 240)


servos = [
    LX16A(10),
    LX16A(11),
    LX16A(12),
    LX16A(20),
    LX16A(21),
    LX16A(22),
]

HOME = np.zeros(6)

def goto_pose(pose: np.ndarray):
    for index, angle in enumerate(pose):
        servos[index].move(signed_to_angle(angle))


goto_pose(HOME)