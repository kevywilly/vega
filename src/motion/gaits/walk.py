import numpy as np

from settings import settings
from src.motion.gaits.gait import Gait


class Walk(Gait):

    def build_steps(self):
        up_down = np.sin(np.radians(np.linspace(0, 180, self.num_steps)))
        x = np.hstack([
            np.sin(np.radians(np.linspace(0, 90, self.num_steps * 1))),
            np.cos(np.radians(np.linspace(0, 90, self.num_steps * 1))),
            np.cos(np.radians(np.linspace(90, 180, self.num_steps * 4))),
        ]) * int(self.stride)
        z = np.hstack([
            np.sin(np.radians(np.linspace(90, 180, self.num_steps))),
            np.zeros(self.num_steps*5)
        ]) * (-self.clearance)

        x = x.reshape((6,-1))
        z = z.reshape((6,-1))

        x1 = np.array([x[0], x[1], x[2], x[3], x[4], x[5]]).flatten()
        x2 = np.array([x[2], x[0], x[1], x[2], x[3], x[4]]).flatten()
        x3 = np.array([x[2], x[3], x[0], x[1], x[2], x[3]]).flatten()
        x4 = np.array([x[2], x[3], x[4], x[0], x[1], x[2]]).flatten()

        z1 = z.flatten()
        z2 = np.roll(z,1,0).flatten()
        z3 = np.roll(z,2,0).flatten()
        z4 = np.roll(z,3,0).flatten()

        y = np.zeros(x1.size)

        self.steps1 = Gait.reshape_steps(np.array([x4,y,z4]), x1.size) # leg 0
        self.steps2 = Gait.reshape_steps(np.array([x2,y,z2]), x1.size) # leg 1
        self.steps3 = Gait.reshape_steps(np.array([x1, y, z1]), x1.size) # leg 2
        self.steps4 = Gait.reshape_steps(np.array([x3,y,z3]), x1.size) # leg 3


if __name__ == "__main__":

    gait = Walk(
        p0=settings.position_ready,
        stride=50,
        clearance=50,
        step_size=1
    )

    gait.plotit()
