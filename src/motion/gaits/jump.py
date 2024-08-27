import numpy as np
from src.motion.gaits.gait import Gait

class Jump(Gait):

    def build_steps(self):
        # Define the up and down motion for jumping
        up_down = np.sin(np.radians(np.linspace(0, 180, self.num_steps))) * self.clearance

        # All legs move up and down together
        x = np.zeros(self.num_steps * 2)
        y = np.zeros(self.num_steps * 2)
        z = np.hstack([up_down, -up_down])

        # Reshape steps for each leg
        self.steps1 = Gait.reshape_steps(np.array([x, y, z]), self.num_steps * 2)
        self.steps2 = self.steps1.copy()
        self.steps3 = self.steps1.copy()
        self.steps4 = self.steps1.copy()

if __name__ == "__main__":
    from settings import settings

    gait = Jump(
        p0=settings.position_ready,
        stride=0,  # No forward movement
        clearance=50,  # Height of the jump
        step_size=1
    )

    gait.plotit()