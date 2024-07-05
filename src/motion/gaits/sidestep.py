import numpy as np

from src.motion.gaits.gait import Gait


class Sidestep(Gait):
    def build_steps(self):
        mag_z = -self.clearance
        mag_y = self.stride

        x = np.repeat(self.zeros,3)
        y = np.hstack([
            self.stride_forward(),
            self.stride_front_to_back(self.num_steps*2),
        ]) * mag_y
        z = np.hstack([
            self.updown(),
            self.zeros
            self.zeros
        ]) * mag_z

        self.steps1 = self.reshape_steps(np.array([x, y, z]), self.num_steps * 3)
        self.steps2 = np.roll(self.steps1, self.num_steps, axis=0)
