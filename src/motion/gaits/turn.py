from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

from settings import settings
from src.motion.gaits.gait import Gait





class Turn(Gait):
    def build_steps(self):
        mag_z = -self.clearance
        mag_y = self.stride

        x = np.zeros(self.num_steps*8)

        y = np.hstack([
            np.sin(np.radians(np.linspace(0, 90, self.num_steps))),
            np.zeros(self.num_steps*3) + 1,
            np.cos(np.radians(np.linspace(0, 90, self.num_steps))),
            np.zeros(self.num_steps*3),
        ]) * -1 * mag_y

        z = np.hstack([
            np.sin(np.radians(np.linspace(0, 180, self.num_steps))),
            np.zeros(self.num_steps*7),
        ]) * mag_z





        front = self.reshape_steps(np.array([x, y, z]), self.num_steps * 8)
        back = self.reshape_steps(np.array([x, -y, z]), self.num_steps * 8)

        self.steps1 = front
        self.steps2 = np.roll(front, self.num_steps, axis=0)
        self.steps3 = np.roll(back, self.num_steps*6, axis=0)
        self.steps4 = np.roll(back, self.num_steps*7, axis=0)

