import numpy as np

from src.motion.gaits.gait import Gait


class Sideways(Gait):
    def build_steps(self):

        mag_z = -self.clearance
        mag_y = self.stride

        x0 = np.zeros(self.num_steps)
        y0 = np.sin(np.radians(np.linspace(45, 90, self.num_steps))) * mag_y
        z0 = np.sin(np.radians(np.linspace(0, 180, self.num_steps))) * mag_z

        x1 = np.zeros(self.num_steps)
        y1 = np.cos(np.radians(np.linspace(90, 180, self.num_steps))) * mag_y
        z1 = np.zeros(self.num_steps)

        self.steps1 = self.reshape_steps(np.array([x0, y0, z0]), self.num_steps)
        self.steps2 = self.reshape_steps(np.array([x1, y1, z1]), self.num_steps)

    def step_generator(self, **kwargs):

        for phase in [0, 1]:
            for i in range(self.steps1.shape[0]):
                s0 = self.steps1[i]
                s1 = self.steps2[i]
                s2 = self.steps1[i]
                s3 = self.steps2[i]

                if phase == 0:
                    yield self.p0 + np.array([s0, s1, s2, s3])
                else:
                    yield self.p0 + np.array([s1, s2, s3, s0])
