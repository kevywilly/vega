from src.motion.gaits.gait import Gait
import numpy as np


class canter(Gait):

    def build_steps(self):
        z_up_down = np.sin(np.radians(np.linspace(45, 180, self.num_steps)))