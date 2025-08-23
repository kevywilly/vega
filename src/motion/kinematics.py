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
    
    def __init__(self, coxa_length: float, femur_length: float, tibia_length: float, 
                 body_width: float, body_length: float):
        """
        Initialize quadruped kinematics
        
        Args:
            coxa_length: Length of coxa segment (hip to femur joint)
            femur_length: Length of femur segment (upper leg)
            tibia_length: Length of tibia segment (lower leg)
            body_width: Width of robot body (left to right)
            body_length: Length of robot body (front to back)
        """
        self.coxa = coxa_length
        self.femur = femur_length
        self.tibia = tibia_length
        self.body_width = body_width
        self.body_length = body_length
        
        # Validate that the leg can reach (femur + tibia must be > coxa for reasonable workspace)
        if self.femur + self.tibia <= self.coxa:
            raise ValueError("Invalid leg dimensions: femur + tibia should be > coxa for adequate workspace")
    
    def inverse_kinematics(self, target_position: np.ndarray) -> np.ndarray:
        """
        Calculate joint angles to reach target end-effector position
        
        Args:
            target_position: [x, y, z] position in leg coordinate frame
            
        Returns:
            Joint angles [coxa_angle, femur_angle, tibia_angle] in radians
            
        Reference: https://robotacademy.net.au/lesson/inverse-kinematics-for-a-2-joint-robot-arm-using-geometry/
        """
        x, y, z = target_position
        
        # Invert x for world coordinate system convention
        x = -x
        
        # Calculate 2D distance in x-z plane for 2-link arm IK
        horizontal_distance = sqrt(x**2 + z**2)
        
        # Check if target is reachable
        max_reach = self.femur + self.tibia
        min_reach = abs(self.femur - self.tibia)
        
        if horizontal_distance > max_reach or horizontal_distance < min_reach:
            raise ValueError(f"Target position unreachable. Distance: {horizontal_distance:.2f}, "
                           f"Valid range: [{min_reach:.2f}, {max_reach:.2f}]")
        
        # Solve 2-link arm in x-z plane using law of cosines
        cos_tibia_angle = (x**2 + z**2 - self.femur**2 - self.tibia**2) / (2 * self.femur * self.tibia)
        cos_tibia_angle = np.clip(cos_tibia_angle, -1.0, 1.0)  # Clamp to valid range
        
        tibia_angle = acos(cos_tibia_angle)
        
        # Calculate femur angle using geometry
        femur_angle = atan2(z, x) - atan2(self.tibia * sin(tibia_angle), 
                                         self.femur + self.tibia * cos(cos_tibia_angle))
        
        # Calculate coxa angle for y-axis rotation
        coxa_angle = atan2(y, horizontal_distance)
        
        return np.array([coxa_angle, femur_angle, tibia_angle])
    
    def forward_kinematics(self, joint_angles: np.ndarray) -> np.ndarray:
        """
        Calculate end-effector position from joint angles
        
        Args:
            joint_angles: [coxa_angle, femur_angle, tibia_angle] in radians
            
        Returns:
            End-effector position [x, y, z] in leg coordinate frame
        """
        coxa_angle, femur_angle, tibia_angle = joint_angles
        
        # Calculate position in x-z plane (2-link arm)
        x_local = self.femur * cos(femur_angle) + self.tibia * cos(femur_angle + tibia_angle)
        z_local = self.femur * sin(femur_angle) + self.tibia * sin(femur_angle + tibia_angle)
        
        # Calculate y position using coxa rotation
        horizontal_distance = sqrt(x_local**2 + z_local**2)
        y_local = horizontal_distance * sin(coxa_angle)
        z_final = horizontal_distance * cos(coxa_angle)
        
        # Invert x back to world coordinates
        return np.array([-x_local, y_local, z_final])
    
    def apply_body_tilt(self, foot_positions: np.ndarray, pitch: float, yaw: float) -> np.ndarray:
        """
        Apply body tilt to foot positions for stability
        
        Args:
            foot_positions: Array of shape (4, 3) with foot positions for [FL, FR, RL, RR]
            pitch: Pitch angle in degrees (positive = nose down)  
            yaw: Yaw angle in degrees (positive = roll right)
            
        Returns:
            Adjusted foot positions with body tilt compensation
        """
        if foot_positions.shape != (4, 3):
            raise ValueError("foot_positions must be shape (4, 3) for [FL, FR, RL, RR] legs")
        
        # Convert angles to radians
        pitch_rad = radians(pitch)
        yaw_rad = radians(yaw)
        
        # Calculate height adjustments for each leg corner
        # Pitch affects front/back legs differently
        pitch_offset = (self.body_length * sin(pitch_rad)) / 2
        
        # Yaw affects left/right legs differently  
        yaw_offset = (self.body_width * sin(yaw_rad)) / 2
        
        # Apply offsets: [FL, FR, RL, RR]
        pitch_multipliers = np.array([1, 1, -1, -1])  # Front legs +, rear legs -
        yaw_multipliers = np.array([1, -1, -1, 1])    # Left legs +, right legs -
        
        adjusted_positions = foot_positions.copy()
        adjusted_positions[:, 2] += (pitch_offset * pitch_multipliers + 
                                   yaw_offset * yaw_multipliers)
        
        return adjusted_positions.astype(int)
    
    def get_leg_workspace(self, num_points: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate the reachable workspace for a leg
        
        Args:
            num_points: Number of points to sample in each dimension
            
        Returns:
            Tuple of (x_coords, y_coords, z_coords) defining workspace boundary
        """
        max_reach = self.femur + self.tibia
        min_reach = abs(self.femur - self.tibia)
        
        # Create spherical coordinates
        theta = np.linspace(0, 2*np.pi, num_points)
        phi = np.linspace(0, np.pi, num_points//2)
        
        x_coords, y_coords, z_coords = [], [], []
        
        # Sample points on workspace boundary
        for r in [min_reach, max_reach]:
            for t in theta:
                for p in phi:
                    x = r * sin(p) * cos(t)
                    y = r * sin(p) * sin(t) 
                    z = r * cos(p)
                    
                    x_coords.append(x)
                    y_coords.append(y) 
                    z_coords.append(z)
        
        return np.array(x_coords), np.array(y_coords), np.array(z_coords)
    
    def validate_joint_limits(self, joint_angles: np.ndarray, 
                            coxa_limits: Tuple[float, float] = (-np.pi/2, np.pi/2),
                            femur_limits: Tuple[float, float] = (-np.pi/2, np.pi/2), 
                            tibia_limits: Tuple[float, float] = (0, np.pi)) -> bool:
        """
        Check if joint angles are within mechanical limits
        
        Args:
            joint_angles: [coxa, femur, tibia] angles in radians
            coxa_limits: (min, max) angles for coxa joint
            femur_limits: (min, max) angles for femur joint  
            tibia_limits: (min, max) angles for tibia joint
            
        Returns:
            True if all angles within limits, False otherwise
        """
        coxa, femur, tibia = joint_angles
        
        return (coxa_limits[0] <= coxa <= coxa_limits[1] and
                femur_limits[0] <= femur <= femur_limits[1] and 
                tibia_limits[0] <= tibia <= tibia_limits[1])


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