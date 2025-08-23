"""
Quadruped Robot Kinematics
Clean implementation for inverse and forward kinematics calculations
"""

import numpy as np
from math import sin, cos, atan2, acos, sqrt, radians
from typing import Tuple


class QuadrupedKinematics:
    """
    Kinematics solver for a quadruped robot with 3-DOF legs
    
    Each leg has:
    - Coxa: Hip joint (rotation around vertical axis)  
    - Femur: Upper leg segment
    - Tibia: Lower leg segment
    """
    
    def __init__(self, coxa, femur, tibia, width, length):
        self.coxa = coxa
        self.femur = femur
        self.tibia = tibia
        self.width = width
        self.length = length

    def inverse_kinematics(self, pos: np.ndarray) -> np.ndarray:
        """ https://robotacademy.net.au/lesson/inverse-kinematics-for-a-2-joint-robot-arm-using-geometry/ """
        x, y, z = pos
        x = -x # invert x for world coordinate positioning

        cos_q2 = (x * x + z * z - self.femur ** 2 - self.tibia ** 2) / (2 * self.femur * self.tibia)
        q2 = acos(cos_q2)
        q1 = atan2(z, x) - atan2(self.tibia * sin(q2), (self.femur + self.tibia * cos_q2))

        q3 = atan2(y, z)

        return np.array([q3, q1, q2])

    def forward_kinematics(self, angles: np.ndarray) -> np.ndarray:
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
        # invert x for world coordinates
        return np.array([-x, 0, z])

    def apply_body_tilt(self, positions: np.ndarray, pitch: float, yaw: float) -> np.ndarray:
        # positive yaw = nose up
        # positive pitch = clockwise
        zx = self.length * np.sin(np.radians(yaw))/2
        zy = self.width * np.sin(np.radians(pitch))/2

        p = positions * 1
        p[:,2] += zx * np.array([1,1,-1,-1]) + zy * np.array([1,-1,-1,1])
        return p.astype(int)


# Example usage and testing
if __name__ == "__main__":
    # Initialize kinematics for typical quadruped dimensions (in mm)
    kinematics = QuadrupedKinematics(
        coxa_length=50,
        femur_length=100, 
        tibia_length=120,
        body_width=200,
        body_length=300
    )
    
    # Test inverse kinematics
    target_pos = np.array([100, 50, -150])  # Target foot position
    try:
        joint_angles = kinematics.inverse_kinematics(target_pos)
        print(f"Target position: {target_pos}")
        print(f"Joint angles (deg): {np.degrees(joint_angles)}")
        
        # Verify with forward kinematics
        calculated_pos = kinematics.forward_kinematics(joint_angles)
        print(f"Calculated position: {calculated_pos}")
        print(f"Error: {np.linalg.norm(target_pos - calculated_pos):.3f} mm")
        
    except ValueError as e:
        print(f"IK Error: {e}")
    
    # Test body tilt
    foot_positions = np.array([
        [120, 100, -140],   # Front left
        [120, -100, -140],  # Front right  
        [-120, -100, -140], # Rear left
        [-120, 100, -140]   # Rear right
    ])
    
    tilted_positions = kinematics.apply_body_tilt(foot_positions, pitch=10, yaw=5)
    print(f"\nOriginal foot positions:\n{foot_positions}")
    print(f"Tilted foot positions:\n{tilted_positions}")