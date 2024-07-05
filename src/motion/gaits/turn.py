import numpy as np

from src.motion.gaits.gait import Gait


class Turn(Gait):
    def build_steps(self):
        clearance = -self.clearance

        stride = -self.stride * self.turn_direction

        step = self.stride_forward() * stride
        back = self.stride_back() * stride
        up_down = self.updown() * clearance
        zeros = self.zeros
        all_zeros = np.repeat(self.zeros, 5)

        print(step.size)
        print(back.size)
        print(up_down.size)

        self.steps1 = np.array([
            all_zeros,
            np.hstack([step, zeros, zeros, zeros, back]),
            np.hstack([up_down, zeros, zeros, zeros, zeros])
        ])

        self.steps2 = np.array([
            all_zeros,
            np.hstack([zeros, step, zeros, zeros, back]),
            np.hstack([zeros, up_down, zeros, zeros, zeros])
        ])

        self.steps3 = np.array([
            all_zeros,
            np.hstack([zeros, zeros, -step, zeros, back]),
            np.hstack([zeros, zeros, up_down, zeros, zeros])
        ])

        self.steps4 = np.array([
            all_zeros,
            np.hstack([zeros, zeros, zeros, -step, back]),
            np.hstack([zeros, zeros, zeros, up_down, zeros])
        ])

        self.steps1 = Gait.reshape_steps(self.steps1, self.num_steps * 5)
        self.steps2 = Gait.reshape_steps(self.steps2, self.num_steps * 5)
        self.steps3 = Gait.reshape_steps(self.steps3, self.num_steps * 5)
        self.steps4 = Gait.reshape_steps(self.steps4, self.num_steps * 5)
