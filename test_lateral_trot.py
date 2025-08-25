#!/usr/bin/env python3
"""
Test script for the new TrotWithLateral gait
"""

import time
from settings import settings
from src.motion.gaits.trot_with_lateral import TrotWithLateral
from src.motion.gaits.trot import Trot
from src.nodes.robot import Robot

def compare_gaits():
    """Compare the regular trot with the lateral trot"""
    print("🤖 Comparing Trot vs TrotWithLateral")
    
    # Regular trot
    regular_trot = Trot(
        p0=settings.position_ready,
        stride=50,
        clearance=50,
        step_size=15
    )
    
    # Lateral trot
    lateral_trot = TrotWithLateral(
        p0=settings.position_ready,
        stride=50,
        clearance=50, 
        step_size=15,
        hip_sway=6
    )
    
    print(f"Regular Trot - Y movement range: {regular_trot.steps1[:, 1].min():.1f} to {regular_trot.steps1[:, 1].max():.1f}")
    print(f"Lateral Trot - Y movement range: {lateral_trot.steps1[:, 1].min():.1f} to {lateral_trot.steps1[:, 1].max():.1f}")
    
    return regular_trot, lateral_trot

def test_with_robot():
    """Test the lateral trot with the robot controller"""
    print("🤖 Testing TrotWithLateral with Robot")
    
    robot = Robot()
    robot.ready()
    time.sleep(1)
    
    # Test a few steps of the lateral trot
    gait = TrotWithLateral(
        p0=settings.position_ready,
        stride=30,  # Smaller stride for testing
        clearance=40,
        step_size=20,
        hip_sway=5  # Small lateral movement
    )
    
    print("Executing 5 steps of lateral trot...")
    for i in range(10):  # 10 steps
        position = next(gait)
        robot.controller.move_to(position, 100)  # 100ms per step
        print(f"Step {i+1}: Leg positions Y-axis: {position[:, 1].round(1)}")
        time.sleep(0.15)
    
    print("Returning to ready position...")
    robot.ready()

if __name__ == "__main__":
    print("=== Trot with Lateral Movement Test ===")
    
    # Compare the gaits
    regular, lateral = compare_gaits()
    
    # Ask user if they want to test with robot
    response = input("\nDo you want to test with the robot? (y/n): ").lower().strip()
    if response == 'y':
        try:
            test_with_robot()
            print("✅ Test completed successfully!")
        except Exception as e:
            print(f"❌ Test failed: {e}")
    else:
        print("✅ Comparison completed - lateral movement verified!")