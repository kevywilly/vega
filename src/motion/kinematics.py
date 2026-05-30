"""
Quadruped Robot Kinematics

Per-leg model: the coxa rotates the leg about the +x (forward) axis into the
(x, radial) plane; the femur/tibia form a 2-link arm that reaches the TRUE in-plane
radial distance r = sqrt(y^2 + z^2) (not z alone). q3 = atan2(y, z) carries the
lateral rotation. All four coxa servos are mounted the same way (NOT mirrored) — the
left/right "outward" direction is handled by the sign of y in the gaits, not here.
See ROBOT.md and docs/ideation/2026-05-30-gait-stability-ideation.md for the full rationale.
"""

import numpy as np
from math import sin, cos, atan2, acos, radians, hypot
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
        
        # Pre-compute constants for vectorized IK
        self._femur_sq = femur ** 2
        self._tibia_sq = tibia ** 2
        self._2_femur_tibia = 2 * femur * tibia

    def inverse_kinematics_vectorized(self, positions: np.ndarray) -> np.ndarray:
        """
        Vectorized inverse kinematics for all 4 legs at once.
        ~4x faster than calling inverse_kinematics in a loop.
        
        Args:
            positions: (4, 3) array of [x, y, z] positions for each leg
            
        Returns:
            (4, 3) array of joint angles [coxa, femur, tibia] for each leg
        """
        # Extract and invert x for world coordinates
        x = -positions[:, 0]
        y = positions[:, 1]
        z = positions[:, 2]

        # The coxa rotates the leg about +x into the (x, radial) plane, so the 2-link
        # femur/tibia reaches the TRUE in-plane radial distance r = sqrt(y^2 + z^2), not z.
        # At y=0, r == z exactly, so the trot regime is unchanged; the correction only
        # grows with lateral offset (~30mm at large y), where the old code under-reached.
        r = np.hypot(y, z)

        # Vectorized IK calculations
        x_sq_r_sq = x * x + r * r
        cos_q2 = (x_sq_r_sq - self._femur_sq - self._tibia_sq) / self._2_femur_tibia
        # Clamp to valid range to avoid NaN from acos
        cos_q2 = np.clip(cos_q2, -1.0, 1.0)
        q2 = np.arccos(cos_q2)

        sin_q2 = np.sin(q2)
        q1 = np.arctan2(r, x) - np.arctan2(
            self.tibia * sin_q2,
            self.femur + self.tibia * cos_q2
        )

        q3 = np.arctan2(y, z)

        return np.column_stack([q3, q1, q2])

    def inverse_kinematics_all_legs(self, positions: np.ndarray, offsets: np.ndarray, format="radians") -> np.ndarray:
        angles = self.inverse_kinematics_vectorized(positions + offsets)
        if format == "degrees":
            return np.degrees(angles).astype(int)
        return angles

    def inverse_kinematics(self, pos: np.ndarray) -> np.ndarray:
        """
        Inverse kinematics (scalar reference; vectorized path is used in production).

        Args:
            pos: Target position [x, y, z]

        Returns:
            Joint angles [coxa_angle, femur_angle, tibia_angle]

        Reference: https://robotacademy.net.au/lesson/inverse-kinematics-for-a-2-joint-robot-arm-using-geometry/
        """
        x, y, z = pos
        x = -x  # invert x for world coordinate positioning

        # 2-link reaches the in-plane radial distance r = sqrt(y^2 + z^2), not z.
        # Identical to the old behavior at y=0; corrects lateral foot placement.
        r = hypot(y, z)

        cos_q2 = (x * x + r * r - self.femur ** 2 - self.tibia ** 2) / (2 * self.femur * self.tibia)
        # Clamp to valid range so out-of-reach targets degrade gracefully instead of
        # raising a math domain error (matches inverse_kinematics_vectorized).
        cos_q2 = max(-1.0, min(1.0, cos_q2))
        q2 = acos(cos_q2)
        q1 = atan2(r, x) - atan2(self.tibia * sin(q2), (self.femur + self.tibia * cos_q2))

        q3 = atan2(y, z)

        return np.array([q3, q1, q2])

    def forward_kinematics(self, angles: np.ndarray) -> np.ndarray:
        """
        Forward kinematics - true 3-DOF inverse of inverse_kinematics().

        Args:
            angles: Joint angles [coxa_angle, femur_angle, tibia_angle]

        Returns:
            End effector position [x, y, z]
        """
        q3, theta1, theta2 = angles

        # Two-link arm in the (x, radial) plane
        x = self.femur * cos(theta1) + self.tibia * cos(theta1 + theta2)
        radial = self.femur * sin(theta1) + self.tibia * sin(theta1 + theta2)

        # Coxa (q3) rotates the radial component about +x back into (y, z). This makes FK a
        # true inverse of IK (round-trips to ~0 for any y), unlike the previous [-x, 0, z]
        # which dropped the coxa rotation and always reported y=0.
        y = radial * sin(q3)
        z = radial * cos(q3)

        # invert x for world coordinates
        return np.array([-x, y, z])

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

        p = positions.astype(float)  # copy + avoid int-array casting error on += float
        p[:, 2] += zx * np.array([1, 1, -1, -1]) + zy * np.array([1, -1, -1, 1])
        return p.astype(int)

    # Additional helper methods that don't change core behavior
    def validate_position(self, pos: np.ndarray) -> bool:
        """Check if position is potentially reachable"""
        x, y, z = pos
        # Reach distance in the 2-link plane = sqrt(x^2 + r^2) with r = sqrt(y^2 + z^2),
        # i.e. the full 3D distance — consistent with the radial convention used in IK.
        distance = np.sqrt(x ** 2 + y ** 2 + z ** 2)
        max_reach = self.femur + self.tibia
        min_reach = abs(self.femur - self.tibia)
        return min_reach <= distance <= max_reach

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


# Quick round-trip demo (proper test suite lives in test/test_kinematics.py)
if __name__ == "__main__":
    robot = Kinematics(coxa=53, femur=102, tibia=114, width=142, length=223)

    for test_pos in (np.array([100, 0, 151]), np.array([80, 90, 120])):
        angles = robot.inverse_kinematics(test_pos)
        reconstructed = robot.forward_kinematics(angles)
        err = np.linalg.norm(test_pos - reconstructed)
        print(f"pos={test_pos}  ik(deg)={np.round(np.degrees(angles), 2)}  "
              f"fk={np.round(reconstructed, 3)}  round-trip err={err:.6f} mm")

    positions = np.array([[100, 50, 140], [100, -50, 140],
                          [-100, -50, 140], [-100, 50, 140]])
    print(f"\nTilted (+x):\n{robot.apply_body_tilt(positions, pitch=10, yaw=5)}")
