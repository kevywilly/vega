import numpy as np

from settings import settings
from src.motion.gaits.gait import Gait


class Trot(Gait):

    def build_steps(self):

        x_forward = np.sin(np.radians(np.linspace(0, 90, self.num_steps)))
        x_back_to_start = np.cos(np.radians(np.linspace(0, 90, self.num_steps)))
        x_kick_back = np.cos(np.radians(np.linspace(90, 90 + 45, self.num_steps * 2)))
        z_up_down = np.sin(np.radians(np.linspace(45, 180, self.num_steps)))
        zeros = np.zeros(self.num_steps)

        x = np.hstack([
            x_forward,
            x_back_to_start,
            x_kick_back,
        ]) * int(self.stride)

        y = np.repeat(zeros,4)

        z = np.hstack([
            z_up_down,
            np.repeat(zeros,3),
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
