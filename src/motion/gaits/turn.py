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
        p1 = Position(self.p0)
        pr = p1.rotated(self.degrees)
        offsets = pr.local - p1.local
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

        l3_x = np.hstack([
            np.sin(np.radians(np.linspace(0, 180, num_steps * 2))) * offsets[2][0],
            np.zeros(num_steps * 2)
        ])
        l3_y = np.hstack([
            np.sin(np.radians(np.linspace(0, 180, num_steps * 2))) * offsets[2][1],
            np.zeros(num_steps * 2),
        ])
        l3_z = np.hstack([
            np.sin(np.radians(np.linspace(0, 180, num_steps))) * mag_z,
            np.zeros(num_steps * 3)
        ])

        l4_x = np.hstack([
            np.zeros(num_steps * 2),
            np.sin(np.radians(np.linspace(0, 180, num_steps * 2))) * offsets[3][0],
        ])
        l4_y = np.hstack([
            np.zeros(num_steps * 2),
            np.sin(np.radians(np.linspace(0, 180, num_steps * 2))) * offsets[3][1],
        ])
        l4_z = np.hstack([
            np.zeros(num_steps * 2),
            np.sin(np.radians(np.linspace(0, 180, num_steps))) * mag_z,
            np.zeros(num_steps),
        ])

        self.steps1 = self.reshape_steps(np.array([l1_x, l1_y, l1_z]), total_steps=num_steps*4)

        self.steps2 = self.reshape_steps(np.array([l2_x, l2_y, l2_z]), total_steps=num_steps*4)

        self.steps3 = self.reshape_steps(np.array([l3_x, l3_y, l3_z]), total_steps=num_steps*4)

        self.steps4 = self.reshape_steps(np.array([l4_x, l4_y, l4_z]), total_steps=num_steps*4)

    def step_generator(self, reverse=False):

        for phase in [0, 1]:
            for i in range(self.steps1.shape[0]):
                s0 = self.steps1[i]
                s1 = self.steps2[i]
                s2 = self.steps1[i]
                s3 = self.steps2[i]

                yield self.p0 + np.array([s0, s1, s2, s3])

