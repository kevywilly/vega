import numpy as np

from settings import settings
from src.motion.gaits.gait import Gait, Gait2


class Walk2(Gait2):

    def build_steps(self):
        x = np.hstack([
            np.sin(np.radians(np.linspace(0, 90, self.num_steps))),
            np.cos(np.radians(np.linspace(0, 90, self.num_steps))),
            np.cos(np.radians(np.linspace(90, 90+45, self.num_steps*3))),
        ]) * self.stride

        y = np.zeros(self.num_steps * 5)

        z = np.hstack([
            np.sin(np.radians(np.linspace(0, 180, self.num_steps))),
            np.zeros(self.num_steps*4)
        ]) * (-self.clearance)
        ar = np.array([x,y,z])

        steps = Gait.reshape_steps(np.array([x,y,z]), x.size)
        self.steps4 = steps
        self.steps2 = np.roll(steps, self.num_steps, axis=0)
        self.steps3 = np.roll(steps, self.num_steps*2, axis=0)
        self.steps1 = np.roll(steps, self.num_steps*3, axis=0)

    def get_offsets(self, index):
        return np.array([self.steps1[index], self.steps2[index], self.steps3[index], self.steps4[index]])



if __name__ == "__main__":

    gait = Walk2(
        p0=settings.position_ready,
        stride=50,
        clearance=50,
        step_size=1
    )

    gait.plotit()
