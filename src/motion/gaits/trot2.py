import numpy as np

from src.motion.gaits.gait import Gait


class Trot2(Gait):
    """
    Trot gait for a quadruped robot.

    Builds a trot gait step sequence.
    """

    def build_steps(self):
        """
        Build the step sequences for the trot gait.
        """
        mag_x = -self.stride
        mag_z = -self.clearance

        num_steps = self.num_steps

        # Building the step sequence for the trot gait
        l1_x = np.round(np.hstack([
            np.sin(np.radians(np.linspace(0, 90, num_steps))),
            np.cos(np.radians(np.linspace(0, 90, num_steps))),
            np.zeros(num_steps),
            np.zeros(num_steps)
        ]) * mag_x)

        l1_y = np.zeros(num_steps * 4)

        l1_z = np.round(np.hstack([
            np.sin(np.radians(np.linspace(0, 180, num_steps))),
            np.zeros(num_steps),
            np.zeros(num_steps),
            np.zeros(num_steps)
        ]) * mag_z)



        """

        l2_x = np.zeros(self.num_steps * 2)

        l2_y = np.zeros(self.num_steps * 2)

        l2_z = np.zeros(self.num_steps * 2)
        """
        # Reshape steps for easy processing
        self.steps1 = self.reshape_steps(np.array([l1_x, l1_y, l1_z]), num_steps * 4)
        self.steps2 = np.roll(self.steps1, num_steps*2, axis=0)
