import numpy as np

from src.motion.gaits.gait import Gait


class Sidestep(Gait):
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

    def get_positions(self, phase: int = 0, index: int = 0):
        offsets = self.p0 + self.get_offsets(index)


        if phase == 0:
            pos = (self.p0 + offsets)
        else:
            pos = (self.p0 + np.roll(offsets, 1, 0))

        return pos
