from abc import ABC, abstractmethod

import numpy as np


class Gait(ABC):

    def __init__(self, p0: np.ndarray, stride=60, clearance=60, step_size=15):
        self.stride = stride
        self.clearance = clearance
        self.step_size = step_size
        self.p0 = p0
        self.num_steps = int(90 / self.step_size)
        self.steps1 = np.zeros(self.num_steps)
        self.steps2 = np.zeros(self.num_steps)
        self.size = 0

        self.build_steps()

    @staticmethod
    def reshape_steps(step: np.ndarray, total_steps: int):
        return step.reshape(-1, total_steps).transpose(1, 0).astype(int)

    @abstractmethod
    def build_steps(self):
        pass

    def step_generator(self, reverse=False):

        for phase in [0, 1]:
            for i in range(self.steps1.shape[0]):
                offsets = np.array([self.steps1[i], self.steps2[i], self.steps1[i], self.steps2[i]])

                if phase == 0:
                    yield self.p0 + offsets
                else:
                    yield self.p0 + np.roll(offsets, 1, 0)
