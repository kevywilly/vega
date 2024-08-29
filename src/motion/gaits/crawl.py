from settings import settings
from src.motion.gaits.gait import Gait
import numpy as np

class Crawl(Gait):
    def __init__(self, p0: np.ndarray = settings.position_ready, stride=30, clearance=20, step_size=5, turn_direction=1, is_reversed=False):
        super().__init__(p0, stride, clearance, step_size, turn_direction, is_reversed)

    def build_steps(self):
        # Define the steps for the crawl gait
        # The crawl gait will have a low clearance and short stride
        num_steps = self.num_steps

        # Define the up and down movement for the legs
        updown = self.updown(num_steps)
        downupdown = self.downupdown(num_steps)

        # Define the forward and backward stride
        stride_forward = self.stride_forward(num_steps)
        stride_back = self.stride_back(num_steps)

        # Build the steps for each leg
        self.steps1 = np.vstack([
            stride_forward * self.stride,
            self.zeros,
            updown * self.clearance
        ]).T

        self.steps2 = np.vstack([
            stride_back * self.stride,
            self.zeros,
            downupdown * self.clearance
        ]).T

        self.steps3 = np.vstack([
            stride_back * self.stride,
            self.zeros,
            downupdown * self.clearance
        ]).T

        self.steps4 = np.vstack([
            stride_forward * self.stride,
            self.zeros,
            updown * self.clearance
        ]).T

        # Reshape the steps for easy processing
        self.steps1 = self.reshape_steps(self.steps1, num_steps * 2)
        self.steps2 = self.reshape_steps(self.steps2, num_steps * 2)
        self.steps3 = self.reshape_steps(self.steps3, num_steps * 2)
        self.steps4 = self.reshape_steps(self.steps4, num_steps * 2)

# Example usage
if __name__ == "__main__":
    crawl_gait = Crawl()
    crawl_gait.plotit()