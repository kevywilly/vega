from abc import ABC, abstractmethod

import numpy as np

class Gait(ABC):
    def __init__(self, p0: np.ndarray, mag_x=60, mag_y=20, mag_z=60, step_size=15):
        self.mag_x = mag_x
        self.mag_y = mag_y
        self.mag_z = mag_z
        self.step_size = step_size
        self.p0 = p0
        self.num_steps = int(90 / self.step_size)
        self.steps1 = np.zeros(self.num_steps)
        self.steps2 = np.zeros(self.num_steps)
        self.steps3 = np.zeros(self.num_steps)
        self.steps4 = np.zeros(self.num_steps)
        self.size = 0

        self.build_steps()

    @abstractmethod
    def build_steps(self):
        pass

    @abstractmethod
    def step_generator(self, reverse=False):

        direction = np.array([-1, 1, 1]) if reverse else np.array([1, 1, 1])

        for phase in [0, 1]:
            for i in range(self.num_steps):
                s0 = self.steps1[i] * direction
                s1 = self.steps2[i] * direction
                if phase == 0:
                    yield np.array([s0, s1, s0, s1]) + self.p0
                else:
                    yield np.array([s1, s0, s1, s0]) + self.p0