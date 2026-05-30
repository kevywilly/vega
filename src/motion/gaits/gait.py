from abc import ABC, abstractmethod
from enum import Enum
from functools import cached_property

import numpy as np

from settings import settings
from src.motion.gaits.gait_params import GaitParams
from src.motion.gaits import trajectories


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

    def __init__(self, p0: np.ndarray = settings.position_ready, params: GaitParams | None = None):

        _params = params or GaitParams()
        self.p0 = p0
        self.pivot_ratio = _params.pivot_ratio
        self.turn_direction = _params.turn_direction
        self.is_reversed = _params.is_reversed
        self.stride = -_params.stride if _params.is_reversed else _params.stride
        self.clearance = _params.clearance
        self.step_size = _params.step_size
        self.hip_sway = _params.hip_sway
        self.num_steps = int(90 / self.step_size)
        self.steps1 = np.zeros(self.num_steps * 2)
        self.steps2 = np.zeros(self.num_steps * 2)
        self.steps3 = None
        self.steps4 = None
        # Canonical per-leg step array, shape (4, N, 3). build_steps() may set this
        # directly (a 4-independent-leg / GaitSpec gait); otherwise it is assembled
        # below from the legacy steps1..steps4 authoring attributes.
        self.steps: np.ndarray | None = None

        self.build_steps()
        if self.steps is None:
            self.steps = self._assemble_steps()
        self.positions = self.p0
        self.index = 0
        self.phase = 0
        self.max_index = self.steps.shape[1]

    # Trajectory-shape helpers. These now delegate to the single source in
    # trajectories.py (the math lives in one place). They remain on Gait because
    # the prowl gait still authors its steps imperatively via these methods; they
    # retire once prowl migrates to GaitSpec (plan item 4).
    def updown(self, num_steps=None, mode: UpdownMode = UpdownMode.fast):
        return trajectories.updown(num_steps or self.num_steps, fast=(mode == self.UpdownMode.fast))

    def downupdown(self, num_steps=None):
        return trajectories.downupdown(num_steps or self.num_steps)

    def stride_forward(self, num_steps=None):
        return trajectories.stride_forward(num_steps or self.num_steps)

    def stride_home(self, num_steps=None):
        return trajectories.stride_home(num_steps or self.num_steps)

    def stride_back(self, num_steps=None):
        return trajectories.stride_back(num_steps or self.num_steps)

    def stride_front_to_back(self, num_steps=None):
        return trajectories.stride_front_to_back(num_steps or self.num_steps)

    @cached_property
    def zeros(self):
        return np.zeros(self.num_steps)

    

    @property
    def size(self):
        return self.steps[0].size

    @property
    def shape(self):
        return self.steps[0].shape

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

    def _assemble_steps(self) -> np.ndarray:
        """Assemble the canonical (4, N, 3) per-leg step array from the legacy
        steps1..steps4 authoring attributes.

        Legs 2 and 3 mirror legs 0 and 1 (the diagonal weld, {0,2} / {1,3}) unless
        steps3/steps4 were populated -- the true 4-independent-leg path used by
        Turn. This reproduces exactly what the previous get_offsets branch emitted.
        """
        if self.steps3 is not None and self.steps4 is not None:
            return np.stack([self.steps1, self.steps2, self.steps3, self.steps4])
        return np.stack([self.steps1, self.steps2, self.steps1, self.steps2])

    def get_offsets(self, index) -> np.ndarray:
        """Per-leg (4, 3) offsets at the given cycle index, indexed straight from
        the canonical step array. 4-leg independence is intrinsic to self.steps --
        there is no steps3-is-None special-casing in the hot path."""
        return self.steps[:, index]

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
