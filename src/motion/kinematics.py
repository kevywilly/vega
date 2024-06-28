from math import sin, atan2, acos

import numpy as np


class Kinematics:
    def __init__(self, coxa, femur, tibia, width, length):
        self.coxa = coxa
        self.femur = femur
        self.tibia = tibia
        self.width = width
        self.length = length

    def ik(self, pos: np.ndarray) -> np.ndarray:
        """ https://robotacademy.net.au/lesson/inverse-kinematics-for-a-2-joint-robot-arm-using-geometry/ """
        x, y, z = pos

        cos_q2 = (x * x + z * z - self.femur ** 2 - self.tibia ** 2) / (2 * self.femur * self.tibia)
        q2 = acos(cos_q2)
        q1 = atan2(z, x) - atan2(self.tibia * sin(q2), (self.femur + self.tibia * cos_q2))

        q3 = atan2(y, z)

        return np.array([q3, q1, q2])

    def fk(self, angles: np.ndarray) -> np.ndarray:
        _, theta1, theta2 = angles
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
        z = self.femur * np.sin(theta1) + self.tibia * np.sin(theta1 + theta2)
        # h = np.sqrt(x**2 + z**2)
        return np.array([x, 0, z])

    def tilt(self, positions: np.ndarray, pitch: float, yaw: float) -> np.ndarray:
        # positive yaw = nose up
        # positive pitch = clockwise
        zx = self.length * np.sin(np.radians(yaw))/2
        zy = self.width * np.sin(np.radians(pitch))/2

        p = positions * 1
        p[:,2] += zx * np.array([1,1,-1,-1]) + zy * np.array([1,-1,-1,1])
        return p.astype(int)

