from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

from settings import settings


class Gait(ABC):
    """
    Abstract base class for defining different gaits for a quadruped robot.

    Attributes:
        p0 (np.ndarray): Initial position.
        stride (int): Stride length.
        clearance (int): Step clearance height.
        step_size (int): Step size angle.
        num_steps (int): Number of steps in a half cycle.
        steps1 (np.ndarray): Array to store step sequence 1.
        steps2 (np.ndarray): Array to store step sequence 2.
    """

    def __init__(self, p0: np.ndarray = settings.position_ready, stride=60, clearance=60, step_size=15,
                 turn_pct: Optional[float] = None,
                 is_reversed=False):

        self.p0 = p0
        self.stride = -stride if is_reversed else stride
        self.clearance = clearance
        self.step_size = step_size
        self.num_steps = int(90 / self.step_size)
        self.steps1 = np.zeros(self.num_steps * 2)
        self.steps2 = np.zeros(self.num_steps * 2)
        self.turn_pct = turn_pct
        self.is_reversed = is_reversed

        self.build_steps()
        self.positions = self.p0
        self.index = 0
        self.phase = 0
        self.max_index = self.steps1.shape[0]


    @staticmethod
    def reshape_steps(step: np.ndarray, total_steps: int) -> np.ndarray:
        """
        Reshape the step array for easy processing.

        Args:
            step (np.ndarray): Array of steps.
            total_steps (int): Total number of steps.

        Returns:
            np.ndarray: Reshaped step array.
        """
        return step.reshape(-1, total_steps).transpose(1, 0).astype(int)

    @abstractmethod
    def build_steps(self):
        """
        Abstract method to build steps for the gait. Must be implemented by subclasses.
        """
        pass

    def get_positions(self, phase: int = 0, index: int = 0):
        offsets = np.array([self.steps1[index], self.steps2[index], self.steps1[index], self.steps2[index]])

        if self.turn_pct > 0:
            offsets[:, 0] *= [1.0, .3, .3, 1.0]
        elif self.turn_pct < 0:
            offsets[:, 0] *= [.3, 1.0, 1.0, .3]

        if phase == 0:
            pos = (self.p0 + offsets)
        else:
            pos = (self.p0 + np.roll(offsets, 1, 0))

        return pos


    def step_generator(self):
        """
        Generator to yield the step positions.

        Yields:
            np.ndarray: Step positions.
        """

        for phase in [0, 1]:
            for i in range(self.steps1.shape[0]):
                yield self.get_positions(phase, i)

    def __iter__(self):
        return self

    def __next__(self):
        self.positions = self.get_positions(self.phase, self.index)
        index = self.index + 1
        if index >= self.max_index:
            self.index = 0
            self.phase = 1 if self.phase == 0 else 0
        else:
            self.index = index
        return self.positions
