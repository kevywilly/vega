from typing import Tuple

import numpy as np


class Calibrator:

    @classmethod
    def get_offsets(cls, euler: Tuple[float, float, float]) -> np.ndarray:
        offsets =  np.zeros((4,3))
        heading, pitch, yaw = euler
        if abs(yaw) < 179:
            if yaw < 0: # raise front
                cls.adjust_front(1, offsets)
            else:
                cls.adjust_rear(1, offsets)
        if abs(pitch) < 0.5:
            if pitch < 0:
                cls.adjust_right(1, offsets)
            else:
                cls.adjust_left(1, offsets)

    @classmethod
    def adjust_rear(cls, value: int, offsets: np.ndarray) -> np.ndarray:
        offsets[2, :] + [0, 0, value]
        offsets[3, :] + [0, 0, value]

    @classmethod
    def adjust_front(cls, value: int, offsets: np.ndarray) -> np.ndarray:
        offsets[0, :] + [0, 0, value]
        offsets[1, :] + [0, 0, value]

    @classmethod
    def adjust_left(cls, value: int, offsets: np.ndarray) -> np.ndarray:
        offsets[1, :] + [0, 0, value]
        offsets[2, :] + [0, 0, value]

    @classmethod
    def adjust_right(cls, value: int, offsets: np.ndarray) -> np.ndarray:
        offsets[0, :] + [0, 0, value]
        offsets[3, :] + [0, 0, value]

