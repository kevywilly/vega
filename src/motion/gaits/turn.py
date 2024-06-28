import numpy as np

from src.interfaces.pose import Position
from src.motion.gaits.gait import Gait
from src.motion.gaits.trot import Trot
from src.motion.gaits.trot2 import Trot2


class Turn(Trot):

    def get_positions(self, phase: int = 0, index: int = 0):
        positions = super().get_positions(phase, index)
        return positions * np.array([[1,1,1],[0.5,1,1],[0.5,1,1],[1,1,1]])