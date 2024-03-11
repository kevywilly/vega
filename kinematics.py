from math import sin, atan2, acos

import numpy as np


class Kinematics:
    def __init__(self, coxa, femur, tibia):
        self.coxa = coxa
        self.femur = femur
        self.tibia = tibia


    def ik(self, pos: np.ndarray):
        """ https://robotacademy.net.au/lesson/inverse-kinematics-for-a-2-joint-robot-arm-using-geometry/ """
        _, x, y = pos
        cosq2 = (x * x + y * y - self.femur ** 2 - self.tibia ** 2) / (2 * self.femur * self.tibia)
        q2 = acos(cosq2)
        q1 = atan2(y, x) - atan2(self.tibia * sin(q2), (self.femur + self.tibia * cosq2))
        return np.array([0, q1, q2])


    def fk(self, angles: np.ndarray):
        _,theta1,theta2 = angles
        """
        Calculate the end effector position (x, y) for a two-link arm given the joint angles (theta1, theta2).

        Args:
        theta1: Angle (in radians) of the first joint
        theta2: Angle (in radians) of the second joint
        link1_length: Length of the first arm link
        link2_length: Length of the second arm link

        Returns:
        x: X-coordinate of the end effector position
        y: Y-coordinate of the end effector position
        """
        x = self.femur * np.cos(theta1) + self.tibia * np.cos(theta1 + theta2)
        y = self.femur * np.sin(theta1) + self.tibia * np.sin(theta1 + theta2)
        return np.array([0, x, y])
