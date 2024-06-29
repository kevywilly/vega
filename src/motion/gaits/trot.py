import numpy as np

from settings import settings
from src.motion.gaits.gait import Gait, Gait2


class Trot(Gait2):

    def build_steps(self):
        x = np.hstack([
            np.sin(np.radians(np.linspace(0, 90, self.num_steps))),
            np.cos(np.radians(np.linspace(0, 90, self.num_steps))),
            np.cos(np.radians(np.linspace(90, 90+45, self.num_steps * 2))),
        ]) * self.stride

        y = np.zeros(self.num_steps * 4)

        z = np.hstack([
            np.sin(np.radians(np.linspace(0, 180, self.num_steps))),
            np.zeros(self.num_steps*3)
        ]) * (-self.clearance)

        self.steps1 = Gait.reshape_steps(np.array([x,y,z]), self.num_steps * 4)
        self.steps2 = np.roll(self.steps1, self.num_steps * 2, axis=0)


if __name__ == "__main__":

    gait = Trot(
        p0=settings.position_ready,
        stride=50,
        clearance=50,
        step_size=1
    )

    gait.plotit()
