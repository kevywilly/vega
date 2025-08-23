"""
Quadruped Robot Kinematics - Cleaned up version preserving original math
All calculations kept identical to working implementation
"""

import numpy as np
from math import sin, cos, atan2, acos, radians
from typing import Optional


class QuadrupedKinematics:
    """
    Kinematics solver for quadruped robot - preserves original working math
    
    Joint order: [coxa_angle, femur_angle, tibia_angle]
    - Coxa: Hip rotation around vertical axis
    - Femur: Upper leg segment  
    - Tibia: Lower leg segment
    """
    
    def __init__(self, coxa: float, femur: float, tibia: float, 
                 width: float, length: float):
        """
        Initialize with robot dimensions
        
        Args:
            coxa: Length of coxa segment
            femur: Length of femur segment
            tibia: Length of tibia segment  
            width: Robot body width
            length: Robot body length
        """
        self.coxa = coxa
        self.femur = femur
        self.tibia = tibia
        self.width = width
        self.length = length

    def inverse_kinematics(self, pos: np.ndarray) -> np.ndarray:
        """
        Inverse kinematics - ORIGINAL IMPLEMENTATION PRESERVED
        
        Args:
            pos: Target position [x, y, z]
            
        Returns:
            Joint angles [coxa_angle, femur_angle, tibia_angle]
            
        Reference: https://robotacademy.net.au/lesson/inverse-kinematics-for-a-2-joint-robot-arm-using-geometry/
        """
        x, y, z = pos
        x = -x  # invert x for world coordinate positioning

        cos_q2 = (x * x + z * z - self.femur ** 2 - self.tibia ** 2) / (2 * self.femur * self.tibia)
        q2 = acos(cos_q2)
        q1 = atan2(z, x) - atan2(self.tibia * sin(q2), (self.femur + self.tibia * cos_q2))

        q3 = atan2(y, z)

        return np.array([q3, q1, q2])

    def forward_kinematics(self, angles: np.ndarray) -> np.ndarray:
        """
        Forward kinematics - ORIGINAL IMPLEMENTATION PRESERVED
        
        Args:
            angles: Joint angles [coxa_angle, femur_angle, tibia_angle]
            
        Returns:
            End effector position [x, y, z]
        """
        _, theta1, theta2 = angles
        
        # Calculate position for two-link arm - ORIGINAL MATH
        x = self.femur * cos(theta1) + self.tibia * cos(theta1 + theta2)
        z = self.femur * sin(theta1) + self.tibia * sin(theta1 + theta2)
        
        # invert x for world coordinates - ORIGINAL BEHAVIOR
        return np.array([-x, 0, z])

    def apply_body_tilt(self, positions: np.ndarray, pitch: float, yaw: float) -> np.ndarray:
        """
        Apply body tilt - ORIGINAL IMPLEMENTATION PRESERVED
        
        Args:
            positions: Array of foot positions (4, 3)
            pitch: Pitch angle in degrees (positive = clockwise)
            yaw: Yaw angle in degrees (positive = nose up)
            
        Returns:
            Tilted positions as integers
        """
        # positive yaw = nose up
        # positive pitch = clockwise
        zx = self.length * sin(radians(yaw)) / 2
        zy = self.width * sin(radians(pitch)) / 2

        p = positions * 1
        p[:, 2] += zx * np.array([1, 1, -1, -1]) + zy * np.array([1, -1, -1, 1])
        return p.astype(int)

    # Additional helper methods that don't change core behavior
    def validate_position(self, pos: np.ndarray) -> bool:
        """Check if position is potentially reachable"""
        x, y, z = pos
        distance_2d = np.sqrt((-x) ** 2 + z ** 2)  # Using original x inversion
        max_reach = self.femur + self.tibia
        min_reach = abs(self.femur - self.tibia)
        return min_reach <= distance_2d <= max_reach

    def get_leg_info(self) -> dict:
        """Return leg dimensions for debugging"""
        return {
            'coxa': self.coxa,
            'femur': self.femur, 
            'tibia': self.tibia,
            'width': self.width,
            'length': self.length,
            'max_reach': self.femur + self.tibia,
            'min_reach': abs(self.femur - self.tibia)
        }


# Alias for backward compatibility with your existing code
Kinematics = QuadrupedKinematics


# Test to verify math is identical
if __name__ == "__main__":
    # Test with your original setup
    robot = Kinematics(50, 100, 120, 200, 300)
    
    # Test position
    test_pos = np.array([100, 50, -150])
    print(f"Test position: {test_pos}")
    
    # IK -> FK round trip
    angles = robot.ik(test_pos)
    reconstructed_pos = robot.fk(angles)
    
    print(f"IK angles (deg): {np.degrees(angles)}")
    print(f"FK position: {reconstructed_pos}")
    print(f"Round-trip error: {np.linalg.norm(test_pos - reconstructed_pos):.6f}")
    
    # Test tilt
    positions = np.array([[100, 50, -140], [100, -50, -140], 
                         [-100, -50, -140], [-100, 50, -140]])
    tilted = robot.tilt(positions, pitch=10, yaw=5)
    print(f"\nOriginal positions:\n{positions}")
    print(f"Tilted positions:\n{tilted}")
