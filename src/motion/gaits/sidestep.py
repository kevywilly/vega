import numpy as np

from src.motion.gaits.gait import Gait


class Sidestep(Gait):
    def build_steps(self):
        mag_z = -self.clearance
        mag_y = self.stride

        x = np.zeros(self.num_steps * 2)
        y = np.hstack([
            np.sin(np.radians(np.linspace(0, 90, self.num_steps))),
            np.cos(np.radians(np.linspace(0, 180, self.num_steps)))
        ]) * mag_y
        z = np.hstack([
            np.sin(np.radians(np.linspace(45, 180, self.num_steps))),
            np.zeros(self.num_steps)
        ]) * mag_z

        self.steps1 = self.reshape_steps(np.array([x, y, z]), self.num_steps * 2)
        self.steps2 = np.roll(self.steps1, self.num_steps, axis=0)
