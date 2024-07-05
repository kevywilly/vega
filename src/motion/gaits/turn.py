from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

from settings import settings
from src.motion.gaits.gait import Gait



class Turn(Gait):
    def build_steps(self):
        mag_z = -self.clearance
        mag_y = -self.stride

        step = np.sin(np.radians(np.linspace(0, 90, self.num_steps))) * mag_y * self.turn_direction
        back = np.cos(np.radians(np.linspace(0, 90, self.num_steps))) * mag_y * self.turn_direction
        up_down = np.sin(np.radians(np.linspace(0, 180, self.num_steps))) * mag_z
        stepped = np.zeros(self.num_steps)
        zero = np.zeros(self.num_steps)
        zeros = np.repeat(zero,5)

        print(step.size)
        print(back.size)
        print(up_down.size)

        self.steps1 = np.array([
            zeros,
            np.hstack([step,stepped,stepped,stepped,back]),
            np.hstack([up_down,np.repeat(zero,4)])
        ])

        self.steps2 = np.array([
            zeros,
            np.hstack([zero, step, stepped, stepped, back]),
            np.hstack([zero, up_down,np.repeat(self.zeros,3)])
        ])

        self.steps3 = np.array([
            zeros,
            np.hstack([np.repeat(zero,2), -step, stepped, back]),
            np.hstack([np.repeat(zero,2), up_down, np.repeat(zero,2)])
        ])

        self.steps4 = np.array([
            zeros,
            np.hstack([np.repeat(zero,3), -step, back]),
            np.hstack([np.repeat(zero,3), up_down, zero])
        ])

        self.steps1 = Gait.reshape_steps(self.steps1, self.num_steps * 5)
        self.steps2 = Gait.reshape_steps(self.steps2, self.num_steps * 5)
        self.steps3 = Gait.reshape_steps(self.steps3, self.num_steps * 5)
        self.steps4 = Gait.reshape_steps(self.steps4, self.num_steps * 5)

