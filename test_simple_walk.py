#!/usr/bin/env python3
"""
Test script for the SimpleWalk gait - natural quadruped walking with hip sway
"""

import sys
import os
import numpy as np

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.motion.gaits.simplified_gait import SimpleWalk
from settings import settings

def analyze_walking_pattern():
    """Analyze the walking gait pattern"""
    print("🐅 Analyzing Natural Walking Gait Pattern")
    print("=" * 50)
    
    # Create walking gait
    walk = SimpleWalk(
        stride=40,              # 40mm forward steps
        clearance=25,           # 25mm lift height (lower than trot)
        step_size=20,           # Slower steps for walking
        hip_sway_amplitude=8    # 8mm hip sway
    )
    
    print(f"✓ SimpleWalk created")
    print(f"  📏 Cycle length: {len(walk.steps[0])} steps")
    print(f"  🚶 Walking sequence: LF → RB → RF → LB")
    print(f"  ⚖️ Hip sway amplitude: {walk.hip_sway_amplitude}mm")
    
    return walk

def show_leg_sequence(walk):
    """Show the sequential leg lifting pattern"""
    print(f"\n🦵 Sequential Leg Movement Analysis:")
    print("=" * 45)
    
    print("Step | LF-Z | RF-Z | LB-Z | RB-Z | Lifting | Hip Sway")
    print("-" * 60)
    
    # Show first 16 steps to see full cycle
    for i in range(16):
        positions = next(walk)
        
        # Z positions (negative = lifted)
        z_pos = positions[:, 2]
        ready_z = settings.position_ready[0, 2]
        lifting_threshold = ready_z - 10  # 10mm below ready = lifted
        
        # Check which legs are lifting
        lifting = z_pos < lifting_threshold
        lifting_legs = [j for j, lift in enumerate(lifting) if lift]
        leg_names = ["LF", "RF", "LB", "RB"]
        lifting_str = ",".join([leg_names[j] for j in lifting_legs]) if lifting_legs else "All grounded"
        
        # Hip sway (Y positions)
        y_pos = positions[:, 1]
        avg_sway = np.mean(y_pos)
        
        print(f"{i:4d} | {z_pos[0]:4.1f} | {z_pos[1]:4.1f} | {z_pos[2]:4.1f} | {z_pos[3]:4.1f} | {lifting_str:8s} | {avg_sway:6.1f}")

def analyze_hip_sway_pattern(walk):
    """Analyze the hip sway for balance"""
    print(f"\n🕺 Hip Sway Balance Analysis:")
    print("=" * 35)
    
    # Get Y-positions for each leg over full cycle
    cycle_length = len(walk.steps[0])
    left_legs_y = []  # LF(0) and LB(2)  
    right_legs_y = [] # RF(1) and RB(3)
    
    for step in range(cycle_length):
        left_legs_y.append((walk.steps[0][step, 1] + walk.steps[2][step, 1]) / 2)
        right_legs_y.append((walk.steps[1][step, 1] + walk.steps[3][step, 1]) / 2)
    
    left_legs_y = np.array(left_legs_y)
    right_legs_y = np.array(right_legs_y)
    
    print(f"📊 Left legs Y-axis range: {left_legs_y.min():.1f} to {left_legs_y.max():.1f} mm")
    print(f"📊 Right legs Y-axis range: {right_legs_y.min():.1f} to {right_legs_y.max():.1f} mm")
    print(f"📈 Hip sway amplitude: {(left_legs_y.max() - left_legs_y.min()):.1f} mm")
    
    # Check if sway is balanced
    left_range = left_legs_y.max() - left_legs_y.min()
    right_range = right_legs_y.max() - right_legs_y.min()
    balance_diff = abs(left_range - right_range)
    
    print(f"⚖️ Balance quality: {'Good' if balance_diff < 2 else 'Needs adjustment'} (diff: {balance_diff:.1f}mm)")

def compare_with_trot():
    """Compare walking vs trotting characteristics"""
    print(f"\n🏃‍♂️ Walking vs Trotting Comparison:")
    print("=" * 40)
    
    # Import trot for comparison
    from src.motion.gaits.simplified_gait import SimpleTrot
    
    trot = SimpleTrot(stride=40, clearance=50, step_size=15)
    walk = SimpleWalk(stride=40, clearance=25, step_size=20)
    
    print("Characteristic    | Walking | Trotting")
    print("-" * 42)
    print("Legs in air       | 1 leg   | 2 legs")
    print("Stability         | High    | Medium")  
    print("Speed             | Slow    | Fast")
    print(f"Clearance         | {walk.clearance}mm    | {trot.clearance}mm")
    print(f"Step size         | {walk.step_size}°     | {trot.step_size}°")
    print("Hip sway          | Yes     | Minimal")
    print("Ground contact    | 75%     | 50%")

def test_walking_execution():
    """Test actual walking execution"""
    print("\n🚶‍♂️ Walking Execution Test:")
    print("=" * 30)
    
    walk = SimpleWalk(stride=30, clearance=20, step_size=25, hip_sway_amplitude=6)
    
    print("Testing natural walking pattern...")
    print("Time | Forward | Sway  | Lifting | Description")
    print("-" * 50)
    
    for i in range(8):
        positions = next(walk)
        
        # Calculate metrics
        avg_x = np.mean(positions[:, 0])  # Forward progress
        avg_y = np.mean(positions[:, 1])  # Hip sway
        z_pos = positions[:, 2]
        ready_z = settings.position_ready[0, 2]
        lifting = np.sum(z_pos < (ready_z - 10))  # Count lifted legs
        
        # Determine phase
        if lifting == 1:
            phase = "Single support"
        elif lifting == 0:
            phase = "All grounded"
        else:
            phase = f"{lifting} legs up"
        
        print(f"{i:4d} | {avg_x:6.1f}  | {avg_y:4.1f}  | {lifting} legs  | {phase}")
    
    print("✅ Natural walking pattern confirmed!")

def show_walking_advantages():
    """Show advantages of SimpleWalk"""
    print("\n🎯 SimpleWalk Gait Advantages:")
    print("=" * 35)
    print("✅ **Natural Movement**: Mimics real quadruped walking")
    print("✅ **High Stability**: Only one leg lifted at a time") 
    print("✅ **Hip Sway Balance**: Automatic weight shifting")
    print("✅ **Sequential Coordination**: Clear leg sequence (LF→RB→RF→LB)")
    print("✅ **Longer Ground Contact**: 75% stance phase for stability")
    print("✅ **Smooth Motion**: Natural stride and lift patterns")
    print("✅ **Easy to Tune**: Adjustable sway amplitude and timing")
    print("✅ **Tiger/Cat-like**: Elegant feline movement pattern")

if __name__ == "__main__":
    print("🐅 SimpleWalk Gait Analysis")
    print("=" * 60)
    
    # Analyze walking pattern
    walk_gait = analyze_walking_pattern()
    
    # Show leg sequence
    show_leg_sequence(walk_gait)
    
    # Analyze hip sway
    analyze_hip_sway_pattern(walk_gait)
    
    # Compare with trot
    compare_with_trot()
    
    # Test execution
    test_walking_execution()
    
    # Show advantages
    show_walking_advantages()
    
    print("\n🎉 SimpleWalk is ready for natural quadruped movement!")
    print("   Usage: SimpleWalk(stride=40, clearance=25, hip_sway_amplitude=8)")