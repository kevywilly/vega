import numpy as np

from settings import settings
from src.motion.gaits.gait import Gait


class Trot(Gait):

    def build_steps(self):
        x = np.hstack([
            np.sin(np.radians(np.linspace(0, 90, self.num_steps))),
            np.cos(np.radians(np.linspace(0, 90, self.num_steps))),
            np.cos(np.radians(np.linspace(90, 90 + 45, self.num_steps * 2))),
        ]) * int(self.stride)

        y = np.zeros(self.num_steps * 4)

        z = np.hstack([
            np.sin(np.radians(np.linspace(20, 180, self.num_steps))),
            np.zeros(self.num_steps * 3)
        ]) * (-self.clearance)

        self.steps1 = Gait.reshape_steps(np.array([x, y, z]), self.num_steps * 4)
        self.steps2 = np.roll(self.steps1, self.num_steps * 2, axis=0)


class TrotSimple(Gait):

    def build_steps(self):
        x_step = np.sin(np.radians(np.linspace(0, 90, self.num_steps)))
        x_back = np.cos(np.radians(np.linspace(0, 90, self.num_steps)))
        x_back2 = np.cos(np.radians(np.linspace(90, 135, self.num_steps)))
        z_step = np.sin(np.radians(np.linspace(0, 180, self.num_steps)))
        zeros = np.zeros(self.num_steps)

        x1 = np.hstack([
            x_step,
            x_back,
            x_back2
        ]) * int(self.stride)
        x2 = np.hstack([
            x_back2,
            x_step,
            x_back
        ]) * int(self.stride)

        y = np.zeros(self.num_steps * 3)

        z1 = np.hstack([
            z_step,
            zeros,
            zeros
        ]) * (-self.clearance)

        z2 = np.hstack([
            zeros,
            z_step,
            zeros
        ]) * (-self.clearance)

        self.steps1 = Gait.reshape_steps(np.array([x1, y, z1]), self.num_steps * 3)
        self.steps2 = Gait.reshape_steps(np.array([x2, y, z2]), self.num_steps * 3)


if __name__ == "__main__":
    gait = Trot(
        p0=settings.position_ready,
        stride=50,
        clearance=50,
        step_size=1
    )

    gait.plotit()
