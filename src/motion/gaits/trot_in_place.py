from src.motion.gaits.gait import Gait
import numpy as np


class TrotInPlace(Gait):

    def build_steps(self):

        x = np.repeat(self.zeros,2)
        y = np.repeat(self.zeros, 2)
        z = np.hstack([self.updown()*(-self.clearance), self.zeros])

        self.steps1 = Gait.reshape_steps(np.array([x, y, z]), self.num_steps * 2)
        self.steps2 = np.roll(self.steps1, self.num_steps, axis=0)