import numpy as np
from src.motion.gaits.gait import Gait

class TigerRun(Gait):
    def build_steps(self):
        # Define the magnitude of the stride and clearance
        mag_z = -self.clearance
        mag_y = self.stride

        # Define the x, y, z coordinates for the steps
        x = np.repeat(self.zeros, 2)
        y = np.hstack([
            self.stride_forward(),
            self.stride_front_to_back(),
        ]) * mag_y
        z = np.hstack([
            self.downupdown(),
            self.zeros
        ]) * mag_z

        # Reshape the steps for the legs
        self.steps1 = self.reshape_steps(np.array([x, y, z]), self.num_steps * 2)
        self.steps2 = np.roll(self.steps1, self.num_steps, axis=0)
        self.steps3 = np.roll(self.steps1, self.num_steps * 2, axis=0)
        self.steps4 = np.roll(self.steps1, self.num_steps * 3, axis=0)

if __name__ == "__main__":
    from settings import settings

    gait = TigerRun(
        p0=settings.position_ready,
        stride=100,  # Increase stride length for a more dynamic run
        clearance=80,  # Increase clearance for higher leg lift
        step_size=10  # Adjust step size for smoother transitions
    )

    gait.plotit()