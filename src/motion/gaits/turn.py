import numpy as np

from src.motion.gaits.gait import Gait


class Turn(Gait):
    def build_steps(self):
        mag_z = -self.clearance
        mag_y = -self.stride

        step = np.sin(np.radians(np.linspace(0, 90, self.num_steps))) * mag_y * self.turn_direction
        back = np.cos(np.radians(np.linspace(0, 90, self.num_steps))) * mag_y * self.turn_direction
        up_down = np.sin(np.radians(np.linspace(0, 180, self.num_steps))) * mag_z
        stepped = np.ones(self.num_steps) * mag_y * self.turn_direction
        zeros = np.zeros(self.num_steps)

        s1 = np.array([
            np.repeat(zeros,5),
            np.hstack([step, np.repeat(stepped,3), back]),
            np.hstack([up_down, np.repeat(zeros,4)])
        ])

        s2 = np.array([
            np.repeat(zeros,5),
            np.hstack([zeros, step, np.repeat(stepped,2), back]),
            np.hstack([zeros, up_down, np.repeat(stepped,3)])
        ])

        s3 = np.array([
            np.repeat(zeros,5),
            np.hstack([np.repeat(zeros,2), -step, -stepped, back]),
            np.hstack([np.repeat(zeros,2), up_down, np.repeat(zeros,2)])
        ])

        s4 = np.array([
            np.repeat(zeros,5),
            np.hstack([np.repeat(zeros,3), -step, back]),
            np.hstack([np.repeat(zeros,3), up_down, zeros])
        ])

        print(s1.shape)
        print(self.num_steps*5)

        self.steps1 = Gait.reshape_steps(s1, self.num_steps*5)
        self.steps2 = Gait.reshape_steps(s2, self.num_steps*5)
        self.steps3 = Gait.reshape_steps(s3, self.num_steps*5)
        self.steps4 = Gait.reshape_steps(s4, self.num_steps*5)
