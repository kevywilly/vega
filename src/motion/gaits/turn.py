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
        ]) * -1 * mag_y * self.turn_direction

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
        stepped = np.zeros(self.num_steps) + 1
        zero = np.zeros(self.num_steps)
        zeros = np.zeros(self.num_steps*5)

        print(step.size)
        print(back.size)
        print(up_down.size)

        self.steps1 = np.array([
            zeros,
            np.hstack([step,stepped,stepped,stepped,back]),
            np.hstack([up_down,zero,zero,zero,zero])
        ])

        self.steps2 = np.array([
            zeros,
            np.hstack([zero, step, stepped, stepped, back]),
            np.hstack([zero, up_down, zero, zero, zero])
        ])

        self.steps3 = np.array([
            zeros,
            np.hstack([zero, zero, -step, stepped, back]),
            np.hstack([zero, zero, up_down, zero, zero])
        ])

        self.steps4 = np.array([
            zeros,
            np.hstack([zero, zero, zero, -step, back]),
            np.hstack([zero, zero, zero, up_down, zero])
        ])

        self.steps1 = Gait.reshape_steps(self.steps1, self.num_steps * 5)
        self.steps2 = Gait.reshape_steps(self.steps2, self.num_steps * 5)
        self.steps3 = Gait.reshape_steps(self.steps3, self.num_steps * 5)
        self.steps4 = Gait.reshape_steps(self.steps4, self.num_steps * 5)




