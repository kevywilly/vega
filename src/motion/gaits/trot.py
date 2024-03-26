import numpy as np

from src.motion.gaits.gait import Gait
import numpy as np

from src.motion.gaits.gait import Gait

class BasicTrot(Gait):
    def build_steps(self):

        l1_x = np.hstack([
            np.sin(np.radians(np.linspace(0, 90, self.num_steps))),
            np.sin(np.radians(np.linspace(90, 180, self.num_steps))),
        ]) * -self.mag_x

        l1_y = np.hstack([
            np.zeros(self.num_steps*2)
        ]) * -self.mag_y

        l1_z = np.hstack([
                np.sin(np.radians(np.linspace(0, 180, self.num_steps))),
                np.hstack(np.zeros(self.num_steps))
        ]) * -self.mag_z

        l2_x = np.hstack([
            np.cos(np.radians(np.linspace(90, 180, self.num_steps * 2))),
        ]) * -self.mag_x

        l2_y = np.hstack([
            np.zeros(self.num_steps*2)
        ]) * -self.mag_y

        l2_z = np.hstack([
                np.zeros(self.num_steps * 2)
        ]) * -self.mag_z

        self.steps1 = np.array([l1_x, l1_y, l1_z]).reshape(-1, self.num_steps * 2).transpose(1, 0).astype(int)

        self.steps2 = np.array([l2_x, l2_y, l2_z]).reshape(-1, self.num_steps * 2).transpose(1, 0).astype(int)

        self.steps3 = self.steps1 #* np.array([-1, -1, 1])

        self.steps4 = self.steps2 #* np.array([-1, -1, 1])

    def step_generator(self, reverse=False):

        for phase in [0, 1]:
            for i in range(self.steps1.shape[0]):
                offsets = np.array([self.steps1[i], self.steps2[i], self.steps3[i],self.steps4[i]])

                if phase == 0:
                    yield self.p0 + offsets
                else:
                    yield self.p0 + np.roll(offsets,1,0)


class Trot(Gait):
    def build_steps(self):

        x0 = np.hstack(
            [
                np.sin(np.radians(np.linspace(45, 90, self.num_steps))) * -self.mag_x,
                np.cos(np.radians(np.linspace(0, 90, self.num_steps))) * -self.mag_x
            ]
        )

        y0 = np.zeros(self.num_steps * 2)

        z0 = np.hstack(
            [
                np.sin(np.radians(np.linspace(90, 180, self.num_steps))) * -self.mag_z,
                np.zeros(int(self.num_steps))
            ]
        )

        x1 = np.cos(np.radians(np.linspace(90, 180, self.num_steps * 2))) * -self.mag_x  # 180
        y1 = np.zeros(self.num_steps * 2)
        z1 = np.zeros(self.num_steps * 2)

        self.steps1 = np.array([x0, y0, z0]).reshape(-1, self.num_steps * 2).transpose(1, 0).astype(int)
        self.steps2 = np.array([x1, y1, z1]).reshape(-1, self.num_steps * 2).transpose(1, 0).astype(int)

    def step_generator(self, reverse=False):

        direction = np.array([-1, 1, 1]) if reverse else np.array([1, 1, 1])

        for phase in [0, 1]:
            for i in range(self.steps1.shape[0]):
                s0 = self.steps1[i] * direction
                s1 = self.steps2[i] * direction
                if phase == 0:
                    yield np.array([s0, s1, s0, s1]) + self.p0
                else:
                    yield np.array([s1, s0, s1, s0]) + self.p0
