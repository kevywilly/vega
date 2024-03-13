import numpy as np


class Pose:
    num_links = 12

    def __init__(self):
        self.positions = np.zeros((4, 3))
        self.target_positions = np.zeros((4,3))
        self.angles = np.zeros((4, 3))
        self.target_angles = np.zeros((4,3))
        self.servo_positions = np.zeros((4,3))
        self.cmd = None

    def at_target(self):
        return bool(sum(sum(self.offsets == self.target_offsets)) == self.num_links)



