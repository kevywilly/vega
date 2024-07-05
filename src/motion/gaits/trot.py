import numpy as np

from settings import settings
from src.motion.gaits.gait import Gait


class Trot(Gait):

    def build_steps(self):
        x = np.hstack([
            self.stride_forward(),
            self.stride_home(),
            self.stride_back(self.num_steps * 2),
        ]) * int(self.stride)

        y = np.repeat(self.zeros, 4)

        z = np.hstack([
            self.updown(),
            np.repeat(self.zeros, 3),
        ]) * (-self.clearance)

        self.steps1 = Gait.reshape_steps(np.array([x, y, z]), self.num_steps * 4)
        self.steps2 = np.roll(self.steps1, self.num_steps * 2, axis=0)


if __name__ == "__main__":
    gait = Trot(
        p0=settings.position_ready,
        stride=50,
        clearance=50,
        step_size=1
    )

    gait.plotit()
