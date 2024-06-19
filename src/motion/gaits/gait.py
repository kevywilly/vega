from abc import ABC, abstractmethod

import numpy as np


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

    def __init__(self, p0: np.ndarray, stride=60, clearance=60, step_size=15):
        self.p0 = p0
        self.stride = stride
        self.clearance = clearance
        self.step_size = step_size
        self.num_steps = int(90 / self.step_size)
        self.steps1 = np.zeros(self.num_steps * 2)
        self.steps2 = np.zeros(self.num_steps * 2)

        self.build_steps()

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

    def step_generator(self, reverse=False):
        """
        Generator to yield the step positions.

        Args:
            reverse (bool): Flag to indicate reverse stepping.

        Yields:
            np.ndarray: Step positions.
        """
        for phase in [0, 1]:
            for i in range(self.steps1.shape[0]):
                offsets = np.array([self.steps1[i], self.steps2[i], self.steps1[i], self.steps2[i]])

                if phase == 0:
                    yield self.p0 + offsets
                else:
                    yield self.p0 + np.roll(offsets, 1, 0)