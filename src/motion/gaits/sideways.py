import numpy as np

from src.motion.gaits.gait import Gait
import numpy as np

from src.motion.gaits.gait import Gait


class Sideways(Gait):

    def build_steps(self):
        x0 = np.zeros(self.num_steps)
        y0 = np.sin(np.radians(np.linspace(45, 90, self.num_steps))) * -self.mag_y
        z0 = np.sin(np.radians(np.linspace(0, 180, self.num_steps))) * -self.mag_z

        x1 = np.zeros(self.num_steps)
        y1 = np.cos(np.radians(np.linspace(90, 180, self.num_steps))) * -self.mag_y
        z1 = np.zeros(self.num_steps)

        self.steps1 = np.array([x0, y0, z0]).reshape(-1, self.num_steps).transpose(1, 0).astype(int)
        self.steps2 = np.array([x1, y1, z1]).reshape(-1, self.num_steps).transpose(1, 0).astype(int)

    def step_generator(self, reverse=False):

        direction = np.array([1, 1, 1]) if reverse else np.array([1, -1, 1])

        for phase in [0, 1]:
            for i in range(self.steps1.shape[0]):
                s0 = self.steps1[i] * direction
                s1 = self.steps2[i] * direction
                s2 = self.steps1[i] * direction * np.array([1,-1,1])
                s3 = self.steps2[i] * direction * np.array([1,-1,1])

                if phase == 0:
                    yield np.array([s0,s1,s2,s3]) + self.p0
                else:
                    yield np.array([s1,s2,s3,s0]) + self.p0