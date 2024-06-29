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
        mag_x = self.stride
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
        self.steps1 = Gait.reshape_steps(np.array([l1_x, l1_y, l1_z]), num_steps * 4)
        self.steps2 = np.roll(self.steps1, num_steps*2, axis=0)


    def get_positions(self, phase: int = 0, index: int = 0):

        pos = self.p0 + np.array([self.steps1[index], self.steps2[index], self.steps1[index], self.steps2[index]])
        turn_factor = 1.0 - self.turn_pct

        if self.turn_pct > 0.0:
            pos[:,0] *= [1.0,turn_factor,turn_factor,1.0]
        elif self.turn_pct < 0.0:
            pos[:, 0] *= [turn_factor, 1.0, 1.0, turn_factor]

        return pos

    def step_generator(self, reverse=False):
        """
        Generator to yield the step positions.

        Args:
            reverse (bool): Flag to indicate reverse stepping.

        Yields:
            np.ndarray: Step positions.
        """
        for i in range(self.steps1.shape[0]):
            yield self.p0 + np.array([self.steps1[i], self.steps2[i], self.steps1[i], self.steps2[i]])
