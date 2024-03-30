import numpy as np

from src.motion.gaits.gait import Gait
import numpy as np

from src.motion.gaits.gait import Gait

class Trot(Gait):

    def build_steps(self):

        mag_x = -self.stride
        mag_z = -self.clearance

        l1_x = np.hstack([
            np.sin(np.radians(np.linspace(0, 90, self.num_steps))),
            np.cos(np.radians(np.linspace(0, 90, self.num_steps))),
        ]) * mag_x

        l1_y = np.zeros(self.num_steps*2)

        l1_z = np.hstack([
                np.sin(np.radians(np.linspace(0, 180, self.num_steps))),
                np.hstack(np.zeros(self.num_steps))
        ]) * mag_z

        l2_x = np.hstack([
            np.cos(np.radians(np.linspace(90, 180, self.num_steps * 2))),
        ]) * mag_x

        l2_y = np.zeros(self.num_steps*2)

        l2_z = np.zeros(self.num_steps * 2)

        self.steps1 = self.reshape_steps(np.array([l1_x, l1_y, l1_z]), self.num_steps * 2)

        self.steps2 = self.reshape_steps(np.array([l2_x, l2_y, l2_z]), self.num_steps * 2)

        self.steps3 = self.steps1

        self.steps4 = self.steps2

    def step_generator(self, reverse=False):

        for phase in [0, 1]:
            for i in range(self.steps1.shape[0]):
                offsets = np.array([self.steps1[i], self.steps2[i], self.steps3[i], self.steps4[i]])

                if phase == 0:
                    yield self.p0 + offsets
                else:
                    yield self.p0 + np.roll(offsets,1,0)

