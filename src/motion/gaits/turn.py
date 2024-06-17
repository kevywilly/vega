import numpy as np

from src.interfaces.pose import Position
from src.motion.gaits.gait import Gait


class Turn(Gait):

    def __init__(self, degrees: float, **kwargs):
        self.degrees = degrees
        super().__init__(**kwargs)

    def build_steps(self):

        mag_z = -self.clearance

        self.num_steps = int(45 / self.step_size)
        position_0 = Position(self.p0)
        position_rotated = position_0.rotated(self.degrees)
        offsets = position_rotated.local - position_0.local
        num_steps = self.num_steps

        l1_x = np.hstack([
            np.sin(np.radians(np.linspace(0, 180, num_steps * 2))) * offsets[0][0],
            np.zeros(num_steps * 2)
        ])
        l1_y = np.hstack([
            np.sin(np.radians(np.linspace(0, 180, num_steps * 2))) * offsets[0][1],
            np.zeros(num_steps * 2),
        ])
        l1_z = np.hstack([
            np.sin(np.radians(np.linspace(0, 180, num_steps))) * mag_z,
            np.zeros(num_steps * 3)
        ])

        l2_x = np.hstack([
            np.zeros(num_steps * 2),
            np.sin(np.radians(np.linspace(0, 180, num_steps * 2))) * offsets[1][0],
        ])
        l2_y = np.hstack([
            np.zeros(num_steps * 2),
            np.sin(np.radians(np.linspace(0, 180, num_steps * 2))) * offsets[1][1],
        ])
        l2_z = np.hstack([
            np.zeros(num_steps * 2),
            np.sin(np.radians(np.linspace(0, 180, num_steps))) * mag_z,
            np.zeros(num_steps),
        ])

        self.steps1 = self.reshape_steps(np.array([l1_x, l1_y, l1_z]), total_steps=num_steps * 4)
        self.steps2 = self.reshape_steps(np.array([l2_x, l2_y, l2_z]), total_steps=num_steps * 4)

