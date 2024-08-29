import numpy as np
from src.motion.gaits.gait import Gait

class TurningGait(Gait):
    def build_steps(self):
        mag_z = -self.clearance
        mag_y = self.stride * self.turn_direction
        mag_x = self.stride * 0.5  # Adjust X stride to enhance turning

        x = np.hstack([
            self.stride_left_to_right(),
            self.stride_right_to_left(),
        ]) * mag_x
        y = np.hstack([
            self.stride_forward(),
            self.stride_front_to_back(),
        ]) * mag_y
        z = np.hstack([
            self.downupdown(),
            self.zeros
        ]) * mag_z

        self.steps1 = self.reshape_steps(np.array([x, y, z]), self.num_steps * 2)
        self.steps2 = np.roll(self.steps1, self.num_steps, axis=0)

    def stride_left_to_right(self):
        return np.cos(np.radians(np.linspace(0, 90, self.num_steps)))

    def stride_right_to_left(self):
        return np.cos(np.radians(np.linspace(90, 0, self.num_steps)))

    def downupdown(self):
        return np.sin(np.radians(np.linspace(0, 180, self.num_steps * 2)))

# Example usage:
# turning_gait = TurningGait(turn_direction=1)  # turn_direction=1 for right turn, -1 for left turn
# turning_gait.build_steps()
# for step in turning_gait.step_generator():
#     print(step)