#!/usr/bin/env python3
"""
Test script for TurnV2 gait.
Run with: python test_turn_v2.py
"""

import time
import sys

# Add project root to path
sys.path.insert(0, '/home/orin/vega')

from settings import settings
from src.motion.gaits.turn_v2 import TurnV2, TurnInPlace
from src.motion.gaits.turn import Turn


def compare_gaits():
    """Compare old Turn vs new TurnV2."""
    print("=" * 60)
    print("Comparing Turn (old) vs TurnV2 (new)")
    print("=" * 60)
    
    old_turn = Turn(stride=30, clearance=40, step_size=15, turn_direction=-1)
    new_turn = TurnV2(stride=30, clearance=40, step_size=15, turn_direction=-1)
    
    print(f"\nOld Turn:")
    print(f"  Steps per cycle: {old_turn.max_index}")
    print(f"  Steps shape: {old_turn.steps1.shape}")
    
    print(f"\nNew TurnV2:")
    print(f"  Steps per cycle: {new_turn.max_index}")
    print(f"  Steps shape: {new_turn.steps1.shape}")
    
    print(f"\nSpeed improvement: {old_turn.max_index / new_turn.max_index:.1f}x faster cycle")


def test_turn_v2_on_robot():
    """Test TurnV2 on actual robot."""
    from src.nodes.robot import Robot
    
    print("\n" + "=" * 60)
    print("Testing TurnV2 on Robot")
    print("=" * 60)
    
    robot = Robot()
    
    # Test parameters - increase stride for more aggressive turn
    turn_params = {
        'stride': 35,      # Increase from default 20
        'clearance': 45,
        'step_size': 12,   # Smaller = smoother
        'pivot_ratio': 0.6  # 0.6 = moderate differential
    }
    
    print(f"\nTurn params: {turn_params}")
    
    try:
        # Ready position
        robot.ready(300)
        time.sleep(0.5)
        
        # Test right turn
        print("\n🔄 Testing RIGHT turn (turn_direction=-1)...")
        gait = TurnV2(**turn_params, turn_direction=-1)
        robot.gait = gait
        robot.moving = True
        
        # Run for ~3 seconds
        cycles = 3 * gait.max_index
        for i in range(cycles):
            position = next(gait)
            robot.controller.move_to(position, 0)
            time.sleep(0.02)  # ~50Hz
        
        robot.moving = False
        robot.ready(200)
        time.sleep(1)
        
        # Test left turn
        print("\n🔄 Testing LEFT turn (turn_direction=1)...")
        gait = TurnV2(**turn_params, turn_direction=1)
        robot.gait = gait
        robot.moving = True
        
        for i in range(cycles):
            position = next(gait)
            robot.controller.move_to(position, 0)
            time.sleep(0.02)
        
        robot.moving = False
        robot.ready(200)
        
        print("\n✅ Turn test complete!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
    finally:
        robot.stop()


def dry_run():
    """Print trajectory without robot."""
    print("\n" + "=" * 60)
    print("Dry Run - TurnV2 Trajectory")
    print("=" * 60)
    
    gait = TurnV2(stride=35, clearance=45, step_size=15, turn_direction=-1, pivot_ratio=0.7)
    
    print(f"\nRight turn trajectory (first cycle):")
    print(f"{'Step':>4} | {'L0 (FR)':^20} | {'L1 (FL)':^20} | {'L2 (BL)':^20} | {'L3 (BR)':^20}")
    print("-" * 95)
    
    for i in range(gait.max_index):
        offsets = gait.get_offsets(i)
        print(f"{i:4d} | {str(offsets[0]):^20} | {str(offsets[1]):^20} | {str(offsets[2]):^20} | {str(offsets[3]):^20}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Test TurnV2 gait')
    parser.add_argument('--robot', action='store_true', help='Run on actual robot')
    parser.add_argument('--dry-run', action='store_true', help='Print trajectory only')
    parser.add_argument('--compare', action='store_true', help='Compare old vs new')
    args = parser.parse_args()
    
    if args.compare or (not args.robot and not args.dry_run):
        compare_gaits()
    
    if args.dry_run:
        dry_run()
    
    if args.robot:
        test_turn_v2_on_robot()
