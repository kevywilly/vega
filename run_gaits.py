#!/usr/bin/env python3
"""
Command-line interface for running simplified gaits on the Vega robot.

Usage examples:
    python run_gaits.py trot --stride 50 --clearance 60
    python run_gaits.py trot-with-lateral --lateral-amplitude 8
    python run_gaits.py walk --stride 30 --hip-sway 10
    python run_gaits.py prowl --stride 20 --clearance 15
    python run_gaits.py turn --direction left --stride 25
    python run_gaits.py jump --clearance 80
    python run_gaits.py sidestep --stride 35
"""

import time
import sys
import os
import click
import numpy as np

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from settings import settings
from src.motion.gaits.simplified_gait import (
    SimpleTrot, SimpleTrotWithLateralFixed, SimpleWalk, SimpleProwl,
    SimpleTurn, SimpleSidestep, SimpleJump
)
from src.nodes.robot import Robot


def run_gait_on_robot(gait, duration_steps=50):
    """Run a gait on the robot for specified number of steps"""
    print(f"🤖 Initializing robot...")
    robot = Robot()
    
    print(f"📍 Moving to ready position...")
    robot.ready()
    time.sleep(1)
    
    print(f"🏃 Starting gait execution for {duration_steps} steps...")
    try:
        for i in range(duration_steps):
            positions = next(gait)
            robot.controller.move_to(positions, 100)  # 100ms per step
            
            if i % 10 == 0:
                print(f"  Step {i+1}/{duration_steps}")
                
        print(f"✅ Gait completed successfully!")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Gait interrupted by user")
    except Exception as e:
        print(f"❌ Error during gait execution: {e}")
    finally:
        print(f"📍 Returning to ready position...")
        robot.ready()
        time.sleep(0.5)


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--list-gaits', '-l', is_flag=True, help='List all available gaits')
def cli(ctx, list_gaits):
    """Vega Robot Simplified Gait Runner
    
    Run different gaits on your Vega quadruped robot using the simplified gait system.
    """
    if list_gaits:
        print("🎯 Available Simplified Gaits:")
        print("=" * 40)
        print("🏃 trot                 - Basic diagonal trot")  
        print("🏃 trot-with-lateral    - Trot with hip sway")
        print("🚶 walk                 - Natural sequential walking")
        print("🐆 prowl                - Stealthy prowling movement")
        print("🔄 turn                 - In-place turning")
        print("↔️  sidestep            - Lateral side-stepping")
        print("🦘 jump                 - Vertical jumping")
        print("\nUse 'python run_gaits.py <gait> --help' for gait-specific options")
        return
    
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


@cli.command()
@click.option('--stride', '-s', default=50, help='Forward stride length (mm)', type=int)
@click.option('--clearance', '-c', default=50, help='Leg lift height (mm)', type=int)
@click.option('--step-size', default=15, help='Step size in degrees (controls speed)', type=int)
@click.option('--steps', default=40, help='Number of steps to execute', type=int)
@click.option('--dry-run', is_flag=True, help='Test gait without robot (simulation)')
def trot(stride, clearance, step_size, steps, dry_run):
    """Run basic diagonal trot gait"""
    print(f"🏃 Running SimpleTrot (stride={stride}, clearance={clearance}, step_size={step_size})")
    
    gait = SimpleTrot(
        p0=settings.position_ready,
        stride=stride,
        clearance=clearance,
        step_size=step_size
    )
    
    if dry_run:
        print("🧪 Dry run - testing gait generation...")
        for i in range(5):
            pos = next(gait)
            print(f"  Step {i}: X_avg={np.mean(pos[:, 0]):.1f}mm")
        print("✅ Gait test successful!")
    else:
        run_gait_on_robot(gait, steps)


@cli.command('trot-with-lateral')
@click.option('--stride', '-s', default=50, help='Forward stride length (mm)', type=int)
@click.option('--clearance', '-c', default=50, help='Leg lift height (mm)', type=int)
@click.option('--step-size', default=15, help='Step size in degrees (controls speed)', type=int)
@click.option('--lateral-amplitude', '-a', default=6, help='Hip sway amplitude (mm)', type=int)
@click.option('--steps', default=40, help='Number of steps to execute', type=int)
@click.option('--dry-run', is_flag=True, help='Test gait without robot (simulation)')
def trot_with_lateral(stride, clearance, step_size, lateral_amplitude, steps, dry_run):
    """Run trot gait with lateral hip movement"""
    print(f"🏃 Running SimpleTrotWithLateral (stride={stride}, clearance={clearance}, lateral={lateral_amplitude})")
    
    gait = SimpleTrotWithLateralFixed(
        p0=settings.position_ready,
        stride=stride,
        clearance=clearance,
        step_size=step_size,
        lateral_amplitude=lateral_amplitude
    )
    
    if dry_run:
        print("🧪 Dry run - testing gait generation...")
        for i in range(5):
            pos = next(gait)
            y_range = f"[{pos[:, 1].min():.1f},{pos[:, 1].max():.1f}]"
            print(f"  Step {i}: X_avg={np.mean(pos[:, 0]):.1f}mm, Y_range={y_range}")
        print("✅ Gait test successful!")
    else:
        run_gait_on_robot(gait, steps)


@cli.command()
@click.option('--stride', '-s', default=35, help='Forward stride length (mm)', type=int)
@click.option('--clearance', '-c', default=25, help='Leg lift height (mm)', type=int)
@click.option('--step-size', default=20, help='Step size in degrees (controls speed)', type=int)
@click.option('--hip-sway', default=8, help='Hip sway amplitude (mm)', type=int)
@click.option('--steps', default=30, help='Number of steps to execute', type=int)
@click.option('--dry-run', is_flag=True, help='Test gait without robot (simulation)')
def walk(stride, clearance, step_size, hip_sway, steps, dry_run):
    """Run natural walking gait with sequential leg movement"""
    print(f"🚶 Running SimpleWalk (stride={stride}, clearance={clearance}, hip_sway={hip_sway})")
    
    gait = SimpleWalk(
        p0=settings.position_ready,
        stride=stride,
        clearance=clearance,
        step_size=step_size,
        hip_sway_amplitude=hip_sway
    )
    
    if dry_run:
        print("🧪 Dry run - testing gait generation...")
        for i in range(5):
            pos = next(gait)
            lifted_legs = sum(1 for z in pos[:, 2] if z < 130)
            print(f"  Step {i}: X_avg={np.mean(pos[:, 0]):.1f}mm, {lifted_legs} legs lifted")
        print("✅ Gait test successful!")
    else:
        run_gait_on_robot(gait, steps)


@cli.command()
@click.option('--stride', '-s', default=25, help='Forward stride length (mm)', type=int)
@click.option('--clearance', '-c', default=15, help='Leg lift height (mm)', type=int)
@click.option('--step-size', default=25, help='Step size in degrees (controls speed)', type=int)
@click.option('--hip-sway', default=12, help='Hip sway amplitude (mm)', type=int)
@click.option('--steps', default=25, help='Number of steps to execute', type=int)
@click.option('--dry-run', is_flag=True, help='Test gait without robot (simulation)')
def prowl(stride, clearance, step_size, hip_sway, steps, dry_run):
    """Run stealthy prowling gait with strong hip sway"""
    print(f"🐆 Running SimpleProwl (stride={stride}, clearance={clearance}, hip_sway={hip_sway})")
    
    gait = SimpleProwl(
        p0=settings.position_ready,
        stride=stride,
        clearance=clearance,
        step_size=step_size,
        hip_sway_amplitude=hip_sway
    )
    
    if dry_run:
        print("🧪 Dry run - testing prowling gait...")
        for i in range(5):
            pos = next(gait)
            y_range = f"[{pos[:, 1].min():.1f},{pos[:, 1].max():.1f}]"
            print(f"  Step {i}: X_avg={np.mean(pos[:, 0]):.1f}mm, Y_range={y_range}")
        print("✅ Prowl test successful!")
    else:
        run_gait_on_robot(gait, steps)


@cli.command()
@click.option('--stride', '-s', default=25, help='Turn step size (mm)', type=int)
@click.option('--clearance', '-c', default=35, help='Leg lift height (mm)', type=int)
@click.option('--step-size', default=15, help='Step size in degrees (controls speed)', type=int)
@click.option('--direction', '-d', type=click.Choice(['left', 'right']), default='right', help='Turn direction')
@click.option('--steps', default=30, help='Number of steps to execute', type=int)
@click.option('--dry-run', is_flag=True, help='Test gait without robot (simulation)')
def turn(stride, clearance, step_size, direction, steps, dry_run):
    """Run in-place turning gait"""
    turn_direction = -1 if direction == 'left' else 1
    print(f"🔄 Running SimpleTurn {direction} (stride={stride}, clearance={clearance})")
    
    gait = SimpleTurn(
        p0=settings.position_ready,
        stride=stride,
        clearance=clearance,
        step_size=step_size,
        turn_direction=turn_direction
    )
    
    if dry_run:
        print("🧪 Dry run - testing turn gait...")
        for i in range(5):
            pos = next(gait)
            y_range = f"[{pos[:, 1].min():.1f},{pos[:, 1].max():.1f}]"
            print(f"  Step {i}: Y_range={y_range} ({'left' if np.mean(pos[:, 1]) < 0 else 'right'} turn)")
        print("✅ Turn test successful!")
    else:
        run_gait_on_robot(gait, steps)


@cli.command()
@click.option('--stride', '-s', default=30, help='Lateral stride length (mm)', type=int)
@click.option('--clearance', '-c', default=40, help='Leg lift height (mm)', type=int)
@click.option('--step-size', default=15, help='Step size in degrees (controls speed)', type=int)
@click.option('--steps', default=20, help='Number of steps to execute', type=int)
@click.option('--dry-run', is_flag=True, help='Test gait without robot (simulation)')
def sidestep(stride, clearance, step_size, steps, dry_run):
    """Run lateral sidestep gait"""
    print(f"↔️ Running SimpleSidestep (stride={stride}, clearance={clearance})")
    
    gait = SimpleSidestep(
        p0=settings.position_ready,
        stride=stride,
        clearance=clearance,
        step_size=step_size
    )
    
    if dry_run:
        print("🧪 Dry run - testing sidestep gait...")
        for i in range(5):
            pos = next(gait)
            y_avg = np.mean(pos[:, 1])
            print(f"  Step {i}: Y_avg={y_avg:.1f}mm (lateral movement)")
        print("✅ Sidestep test successful!")
    else:
        run_gait_on_robot(gait, steps)


@cli.command()
@click.option('--clearance', '-c', default=60, help='Jump height (mm)', type=int)
@click.option('--step-size', default=20, help='Step size in degrees (controls speed)', type=int)
@click.option('--jumps', default=5, help='Number of jumps to execute', type=int)
@click.option('--dry-run', is_flag=True, help='Test gait without robot (simulation)')
def jump(clearance, step_size, jumps, dry_run):
    """Run vertical jumping gait"""
    print(f"🦘 Running SimpleJump (clearance={clearance}, jumps={jumps})")
    
    gait = SimpleJump(
        p0=settings.position_ready,
        clearance=clearance,
        step_size=step_size
    )
    
    if dry_run:
        print("🧪 Dry run - testing jump gait...")
        for i in range(8):
            pos = next(gait)
            z_avg = np.mean(pos[:, 2])
            print(f"  Step {i}: Z_avg={z_avg:.1f}mm ({'up' if z_avg > 145 else 'down'})")
        print("✅ Jump test successful!")
    else:
        # For jumps, execute multiple complete jump cycles
        steps_per_jump = len(gait.steps1)
        total_steps = jumps * steps_per_jump
        run_gait_on_robot(gait, total_steps)


if __name__ == '__main__':
    print("🤖 Vega Robot - Simplified Gait Runner")
    print("=" * 40)
    cli()