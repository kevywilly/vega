from typing import Optional, Dict

import numpy as np

from config import DIMS

_quadrant_matrix = np.array([[1, 1, 1], [1, -1, 1], [-1, -1, 1], [-1, 1, 1]])
_dimensions = np.array([DIMS.LENGTH / 2, DIMS.WIDTH / 2, 0])


def _3d_rotate(corners: np.ndarray, degrees: float):
    """
    rotation_matrix = np.array([
    [np.cos(theta), -np.sin(theta), 0],
    [np.sin(theta), np.cos(theta), 0],
    [0, 0, 1]
    ])
    """
    angle_rad = np.radians(degrees)
    rotation_matrix = np.array([
        [np.cos(angle_rad), -np.sin(angle_rad), 0],
        [np.sin(angle_rad), np.cos(angle_rad), 0],
        [0, 0, 1]
    ])
    return np.dot(rotation_matrix, corners.T).T


class Position:
    def __init__(self, local: np.ndarray, world: Optional[np.ndarray] = None):
        self.local = local
        self.world = (self.local + _dimensions) * _quadrant_matrix

    @classmethod
    def from_world(cls, world: np.ndarray):
        return cls(local=world / _quadrant_matrix - _dimensions, world=world)

    @classmethod
    def from_local(cls, local: np.ndarray):
        return cls(local)

    def rotated(self, degrees):
        p = Position.from_world(_3d_rotate(self.world, degrees))
        return p


class Pose:
    num_links = 12

    def __init__(self):
        self.positions = np.zeros((4, 3))
        self.target_positions = np.zeros((4, 3))
        self.angles = np.zeros((4, 3))
        self.target_angles = np.zeros((4, 3))

        self.cmd = None


    @property
    def servos(self) -> np.ndarray:
        if self.cmd:
            return np.ndarray(self.cmd.values()).reshape(4,3)
        else:
            return np.zeros((4,3))

    @property
    def json(self) -> Dict:
        return {
            "positions": self.positions.tolist(),
            "angles": np.degrees(self.angles).astype(int).tolist(),
            #"servos": self.servos.tolist()
        }

    @property
    def table(self):
        return np.vstack((np.round(np.degrees(self.angles)))).tolist()
        #return list(np.vstack((self.positions, np.round(np.degrees(self.angles)))).flatten())

    def __repr__(self):
        return f"""POS: {self.positions.tolist()}"""

