from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

from settings import settings
from src.motion.gaits.gait import Gait





class Turn(Gait):
    def build_steps(self):
        mag_z = -self.clearance
        mag_y = self.stride

        x = np.zeros(self.num_steps*2)
        y1 = np.hstack([
            np.sin(np.radians(np.linspace(45, 90, self.num_steps))),
            np.cos(np.radians(np.linspace(90, 180, self.num_steps)))
        ]) * mag_y
        z = np.hstack([
            np.sin(np.radians(np.linspace(0, 180, self.num_steps))),
            np.zeros(self.num_steps)
        ]) * mag_z

        y2 = np.hstack([
            np.cos(np.radians(np.linspace(90, 180, self.num_steps))),
            np.sin(np.radians(np.linspace(45, 90, self.num_steps))),
        ]) * -mag_y

        self.steps1 = self.reshape_steps(np.array([x, y1, z]), self.num_steps * 2)
        self.steps2 = self.reshape_steps(np.array([x, y1, z]), self.num_steps * 2)
        self.steps3 = self.reshape_steps(np.array([x, y2, z]), self.num_steps * 2)
        self.steps4 = self.reshape_steps(np.array([x, y2, z]), self.num_steps * 2)

