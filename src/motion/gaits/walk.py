import numpy as np


class Walk:
    def __init__(self, mag_x=60, mag_y=20, mag_z=60, step_size=30):
        self.mag_x = mag_x
        self.mag_y = mag_y
        self.mag_z = mag_z
        step_size = step_size

        phase1_x = np.sin(np.radians(np.arange(0, 90, step_size))) * self.mag_x  # 90
        phase2_x = np.sin(np.radians(np.arange(90, 180, step_size))) * mag_x  # 90
        phase1_z = np.sin(np.radians(np.arange(0, 180, step_size * 2))) * self.mag_x  # 90
        phase2_z = np.zeros(int(90 / step_size))  # 90

        self.x = np.hstack([phase1_x, phase2_x])
        self.y = np.full(self.x.size, -mag_y)
        self.z = np.hstack([phase1_z, phase2_z])

        phase3_x = np.cos(np.radians(np.arange(90, 180, step_size / 2))) * self.mag_x
        phase3_y = np.full(phase3_x.size, -mag_y)
        phase3_z = np.zeros(phase3_x.size)

        self.x2 = phase3_x
        self.y2 = phase3_y
        self.z2 = phase3_z

        self.steps1 = np.array([self.x, self.y, self.z])
        self.steps1 = -self.steps1.reshape(-1, self.x.size).transpose(1, 0).astype(int)

        self.steps2 = np.array([self.x2, self.y2, self.z2])
        self.steps2 = -self.steps2.reshape(-1, self.x2.size).transpose(1, 0).astype(int)
