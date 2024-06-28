import numpy as np

from src.motion.gaits.gait import Gait


class Trot(Gait):
    """
    Trot gait for a quadruped robot.

    Builds a trot gait step sequence.
    """

    def get_positions(self, phase: int = 0, index: int = 0):
        positions = super().get_positions(phase, index)

        if self.turn_pct == 0.0:
            return positions

        if self.turn_pct < 0:
            return positions * np.array([
                [1-self.turn_pct,1,1],
                [1,1,1],
                [1,1,1],
                [1-self.turn_pct,1,1]
            ])
        else:
            return positions * np.array([
                [1, 1, 1],
                [1-self.turn_pct,1,1],
                [1-self.turn_pct,1,1],
                [1, 1, 1]
            ])

    def build_steps(self):
        """
        Build the step sequences for the trot gait.
        """
        mag_x = -self.stride
        mag_z = -self.clearance

        # Building the step sequence for the trot gait
        l1_x = np.hstack([
            np.sin(np.radians(np.linspace(0, 90, self.num_steps))),
            np.cos(np.radians(np.linspace(0, 90, self.num_steps))),
        ]) * mag_x

        l1_y = np.zeros(self.num_steps * 2)

        l1_z = np.hstack([
            np.sin(np.radians(np.linspace(0, 180, self.num_steps))),
            np.zeros(self.num_steps)
        ]) * mag_z

        l2_x = np.hstack([
            np.cos(np.radians(np.linspace(90, 180, self.num_steps * 2))),
        ]) * mag_x

        l2_y = np.zeros(self.num_steps * 2)

        l2_z = np.zeros(self.num_steps * 2)

        # Reshape steps for easy processing
        self.steps1 = self.reshape_steps(np.array([l1_x, l1_y, l1_z]), self.num_steps * 2)
        self.steps2 = self.reshape_steps(np.array([l2_x, l2_y, l2_z]), self.num_steps * 2)
