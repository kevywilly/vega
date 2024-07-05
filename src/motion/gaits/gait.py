from abc import ABC, abstractmethod
from enum import Enum
from functools import cached_property

import matplotlib.pyplot as plt
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

    class UpdownMode(Enum):
        normal = 0
        fast = 1

    def updown(self, num_steps=None):
        return np.sin(np.radians(np.linspace(45, 180, num_steps or self.num_steps)))

    def stride_forward(self, num_steps=None):
        return np.sin(np.radians(np.linspace(0, 90, num_steps or self.num_steps)))

    def stride_home(self, num_steps=None):
        return np.cos(np.radians(np.linspace(0, 90, num_steps or self.num_steps)))

    def stride_back(self, num_steps=None):
        return np.cos(np.radians(np.linspace(90, 180, num_steps or self.num_steps)))

    def stride_front_to_back(self, num_steps=None):
        return np.cos(np.radians(np.linspace(0, 180, num_steps or self.num_steps)))

    @cached_property
    def zeros(self):
        return np.zeros(self.num_steps)

    def __init__(self, p0: np.ndarray = settings.position_ready, stride=60, clearance=60, step_size=15,
                 turn_direction=1,
                 is_reversed=False):

        self.p0 = p0
        self.stride = -stride if is_reversed else stride
        self.clearance = clearance
        self.step_size = step_size
        self.num_steps = int(90 / self.step_size)
        self.steps1 = np.zeros(self.num_steps * 2)
        self.steps2 = np.zeros(self.num_steps * 2)
        self.steps3 = None
        self.steps4 = None
        self.turn_direction = turn_direction
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

    def get_offsets(self, index) -> np.ndarray:

        if self.steps3 is not None and self.steps4 is not None:
            return np.array([self.steps1[index], self.steps2[index], self.steps3[index], self.steps4[index]])
        else:
            return np.array([self.steps1[index], self.steps2[index], self.steps1[index], self.steps2[index]])

    def get_positions(self, phase: int = 0, index: int = 0):
        return self.p0 + self.get_offsets(index)

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

    def plotit(self):
        print("leg 1")
        plt.plot(self.steps1, label=["s1_x", "s1_y", "s1_z"])
        plt.legend()
        plt.show()

        print("leg 2")
        plt.plot(self.steps2, label=["s2_x", "s2_y", "s2_z"])
        plt.legend()
        plt.show()

        if self.steps3 is not None:
            print("leg 3")
            plt.plot(self.steps3, label=["s3_x", "s3_y", "s3_z"])
            plt.legend()
            plt.show()

        if self.steps4 is not None:
            print("leg 4")
            plt.plot(self.steps4, label=["s4_x", "s4_y", "s4_z"])
            plt.legend()
            plt.show()
