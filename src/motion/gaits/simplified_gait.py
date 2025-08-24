"""
Simplified Gait System - Making gait creation much easier and more intuitive

Key improvements:
1. Declarative leg movement definitions
2. Automatic phase management
3. Built-in common movement patterns
4. Clear leg coordination specification
"""

import numpy as np
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Callable, Dict
from settings import settings


class LegPhase(Enum):
    """Define common leg groupings for gaits"""
    ALL = "all"           # All legs together (jump)
    DIAGONAL = "diagonal"  # Diagonal pairs (trot)
    LATERAL = "lateral"    # Left/right pairs (pace)
    SEQUENTIAL = "sequential"  # One leg at a time (walk)


class MovementPattern:
    """Pre-built movement patterns that can be combined"""
    
    @staticmethod
    def lift(steps: int, height: float = 1.0) -> np.ndarray:
        """Standard lift pattern - up and down"""
        return np.sin(np.linspace(0, np.pi, steps)) * height
    
    @staticmethod
    def stride_forward(steps: int, distance: float = 1.0) -> np.ndarray:
        """Forward stride pattern"""
        return np.sin(np.linspace(0, np.pi/2, steps)) * distance
    
    @staticmethod
    def stride_back(steps: int, distance: float = 1.0) -> np.ndarray:
        """Backward return pattern"""
        return np.cos(np.linspace(0, np.pi/2, steps)) * distance
    
    @staticmethod
    def step_cycle(steps: int, distance: float = 1.0) -> np.ndarray:
        """Complete forward-back cycle"""
        half_steps = steps // 2
        return np.concatenate([
            MovementPattern.stride_forward(half_steps, distance),
            MovementPattern.stride_back(half_steps, distance)
        ])
    
    @staticmethod
    def lateral_sway(steps: int, amplitude: float = 1.0) -> np.ndarray:
        """Lateral swaying motion"""
        return np.sin(np.linspace(0, 2*np.pi, steps)) * amplitude
    
    @staticmethod
    def zero(steps: int) -> np.ndarray:
        """No movement"""
        return np.zeros(steps)


@dataclass
class LegMovement:
    """Define movement for a single axis of a leg"""
    x: Callable[[int], np.ndarray] = None  # Forward/back movement function
    y: Callable[[int], np.ndarray] = None  # Lateral movement function  
    z: Callable[[int], np.ndarray] = None  # Up/down movement function
    phase_shift: int = 0  # Phase shift in steps


class SimplifiedGait(ABC):
    """
    Much simpler gait definition system.
    
    Instead of manually building arrays, define:
    1. Movement patterns for each axis
    2. Which legs use which patterns
    3. Phase relationships
    """
    
    def __init__(self, p0: np.ndarray = None, stride: float = 50, 
                 clearance: float = 50, step_size: float = 15, **kwargs):
        self.p0 = p0 if p0 is not None else settings.position_ready
        self.stride = stride
        self.clearance = clearance
        self.step_size = step_size
        self.num_steps = int(90 / step_size)
        
        # Build the gait
        self.leg_movements = self.define_leg_movements()
        self.steps = self._build_steps()
        
        # Iterator state
        self.index = 0
        self.positions = self.p0
    
    @abstractmethod
    def define_leg_movements(self) -> Dict[int, LegMovement]:
        """
        Define movement for each leg (0-3).
        Return dict mapping leg number to LegMovement.
        """
        pass
    
    def _build_steps(self) -> Dict[int, np.ndarray]:
        """Build step arrays from leg movement definitions"""
        steps = {}
        total_steps = self.num_steps * 4  # Assume 4-phase cycle
        
        for leg_num, movement in self.leg_movements.items():
            # Generate movement for each axis
            x = movement.x(total_steps) if movement.x else MovementPattern.zero(total_steps)
            y = movement.y(total_steps) if movement.y else MovementPattern.zero(total_steps)
            z = movement.z(total_steps) if movement.z else MovementPattern.zero(total_steps)
            
            # Apply phase shift
            if movement.phase_shift > 0:
                x = np.roll(x, movement.phase_shift)
                y = np.roll(y, movement.phase_shift)
                z = np.roll(z, movement.phase_shift)
            
            # Stack into (steps, 3) array
            steps[leg_num] = np.column_stack([x, y, z])
        
        return steps
    
    def get_positions(self, index: int) -> np.ndarray:
        """Get positions for all legs at given step index"""
        positions = self.p0.copy()
        for leg_num in range(4):
            if leg_num in self.steps:
                step_idx = index % len(self.steps[leg_num])
                positions[leg_num] += self.steps[leg_num][step_idx]
        return positions
    
    def __iter__(self):
        return self
    
    def __next__(self):
        positions = self.get_positions(self.index)
        self.index = (self.index + 1) % len(next(iter(self.steps.values())))
        return positions


# Example implementations using the simplified system

class SimpleTrot(SimplifiedGait):
    """Trot gait using simplified system"""
    
    def define_leg_movements(self) -> Dict[int, LegMovement]:
        cycle_steps = self.num_steps * 4
        half_cycle = self.num_steps * 2
        
        # Forward stride pattern
        def forward_stride(steps):
            return MovementPattern.step_cycle(steps, self.stride)
        
        # Lift pattern during stance
        def lift_pattern(steps):
            pattern = np.zeros(steps)
            # Lift during first quarter of cycle
            lift_steps = self.num_steps
            pattern[:lift_steps] = MovementPattern.lift(lift_steps, -self.clearance)
            return pattern
        
        return {
            0: LegMovement(x=forward_stride, z=lift_pattern, phase_shift=0),      # Front left
            1: LegMovement(x=forward_stride, z=lift_pattern, phase_shift=half_cycle),  # Front right  
            2: LegMovement(x=forward_stride, z=lift_pattern, phase_shift=half_cycle),  # Back left
            3: LegMovement(x=forward_stride, z=lift_pattern, phase_shift=0),      # Back right
        }


class SimpleTrotWithLateral(SimplifiedGait):
    """Trot with lateral movement using simplified system"""
    
    def __init__(self, lateral_amplitude: float = 8, **kwargs):
        self.lateral_amplitude = lateral_amplitude
        super().__init__(**kwargs)
    
    def define_leg_movements(self) -> Dict[int, LegMovement]:
        cycle_steps = self.num_steps * 4
        half_cycle = self.num_steps * 2
        
        def forward_stride(steps):
            return MovementPattern.step_cycle(steps, self.stride)
        
        def lift_pattern(steps):
            pattern = np.zeros(steps)
            lift_steps = self.num_steps
            pattern[:lift_steps] = MovementPattern.lift(lift_steps, -self.clearance)
            return pattern
        
        def lateral_left(steps):
            return MovementPattern.lateral_sway(steps, self.lateral_amplitude)
        
        def lateral_right(steps):
            return MovementPattern.lateral_sway(steps, -self.lateral_amplitude)
        
        return {
            0: LegMovement(x=forward_stride, y=lateral_left, z=lift_pattern, phase_shift=0),
            1: LegMovement(x=forward_stride, y=lateral_right, z=lift_pattern, phase_shift=half_cycle),
            2: LegMovement(x=forward_stride, y=lateral_left, z=lift_pattern, phase_shift=half_cycle),
            3: LegMovement(x=forward_stride, y=lateral_right, z=lift_pattern, phase_shift=0),
        }


class SimpleJump(SimplifiedGait):
    """Jump gait - all legs together"""
    
    def define_leg_movements(self) -> Dict[int, LegMovement]:
        def jump_up_down(steps):
            half_steps = steps // 2
            up = MovementPattern.lift(half_steps, self.clearance)
            down = MovementPattern.lift(half_steps, -self.clearance)
            return np.concatenate([up, down])
        
        # All legs do the same movement
        movement = LegMovement(z=jump_up_down)
        return {0: movement, 1: movement, 2: movement, 3: movement}


class SimpleSidestep(SimplifiedGait):
    """Sidestep gait using simplified system"""
    
    def define_leg_movements(self) -> Dict[int, LegMovement]:
        cycle_steps = self.num_steps * 2
        half_cycle = self.num_steps
        
        def lateral_step(steps):
            return MovementPattern.step_cycle(steps, self.stride)
        
        def lift_pattern(steps):
            pattern = np.zeros(steps)
            lift_steps = self.num_steps
            pattern[:lift_steps] = MovementPattern.lift(lift_steps, -self.clearance)
            return pattern
        
        return {
            0: LegMovement(y=lateral_step, z=lift_pattern, phase_shift=0),
            1: LegMovement(y=lateral_step, z=lift_pattern, phase_shift=half_cycle),
            2: LegMovement(y=lateral_step, z=lift_pattern, phase_shift=half_cycle),
            3: LegMovement(y=lateral_step, z=lift_pattern, phase_shift=0),
        }


class SimpleTurn(SimplifiedGait):
    """
    Simplified in-place turning gait.
    
    Much cleaner than the existing Turn implementation:
    - Uses diagonal leg coordination (like trot)
    - Left legs step one direction, right legs step opposite
    - Creates efficient rotation around robot center
    - Only ~15 lines vs ~100 lines in original
    """
    
    def __init__(self, turn_direction: int = 1, **kwargs):
        """
        Initialize turn gait.
        
        Args:
            turn_direction: 1 for right turn, -1 for left turn
            **kwargs: Standard gait parameters
        """
        self.turn_direction = turn_direction
        super().__init__(**kwargs)
    
    def define_leg_movements(self) -> Dict[int, LegMovement]:
        cycle_steps = self.num_steps * 2
        half_cycle = self.num_steps
        
        # For turning: left legs move one way, right legs move opposite way
        # This creates rotation around the center of the robot
        def left_turn_step(steps):
            """Left legs step outward for right turn"""
            return MovementPattern.step_cycle(steps, self.stride * self.turn_direction)
        
        def right_turn_step(steps):
            """Right legs step inward for right turn"""
            return MovementPattern.step_cycle(steps, -self.stride * self.turn_direction)
        
        def lift_pattern(steps):
            """Standard lift pattern during step cycle"""
            pattern = np.zeros(steps)
            lift_steps = self.num_steps
            pattern[:lift_steps] = MovementPattern.lift(lift_steps, -self.clearance)
            return pattern
        
        return {
            # Left side legs (0=front-left, 2=back-left)
            0: LegMovement(y=left_turn_step, z=lift_pattern, phase_shift=0),
            2: LegMovement(y=left_turn_step, z=lift_pattern, phase_shift=half_cycle),
            
            # Right side legs (1=front-right, 3=back-right)  
            1: LegMovement(y=right_turn_step, z=lift_pattern, phase_shift=half_cycle),
            3: LegMovement(y=right_turn_step, z=lift_pattern, phase_shift=0),
        }


class SimpleWalk(SimplifiedGait):
    """
    Natural walking gait with sequential leg movement and hip sway.
    
    Mimics natural quadruped walking like tigers/cats:
    - Sequential leg lifting (one at a time)
    - Hip sway for balance and natural movement
    - Longer ground contact phases for stability
    - Body weight shifts toward supporting legs
    """
    
    def __init__(self, hip_sway_amplitude: float = 12, **kwargs):
        """
        Initialize walking gait.
        
        Args:
            hip_sway_amplitude: Amount of lateral hip movement (mm)
            **kwargs: Standard gait parameters
        """
        self.hip_sway_amplitude = hip_sway_amplitude
        super().__init__(**kwargs)
    
    def define_leg_movements(self) -> Dict[int, LegMovement]:
        # Walking uses 4-phase cycle (one leg lifts per phase)
        cycle_steps = self.num_steps * 4
        quarter_cycle = self.num_steps
        
        # Walking sequence: LF -> RB -> RF -> LB (classic quadruped pattern)
        phase_shifts = {
            0: 0,                    # Left Front (LF) - starts first
            3: quarter_cycle,        # Right Back (RB) - opposite diagonal  
            1: quarter_cycle * 2,    # Right Front (RF) - next
            2: quarter_cycle * 3,    # Left Back (LB) - completes cycle
        }
        
        def forward_stride(steps):
            """Forward walking stride - longer ground contact than trot"""
            # Walking has longer stance phase (75% ground, 25% air)
            swing_steps = int(steps * 0.25)  # 25% swing
            stance_steps = steps - swing_steps  # 75% stance
            
            # Swing phase: lift and move forward
            swing = MovementPattern.step_cycle(swing_steps * 4, self.stride)[:swing_steps] 
            # Stance phase: gradual backward movement as body moves forward
            stance = np.linspace(self.stride * 0.3, -self.stride * 0.3, stance_steps)
            
            result = np.concatenate([swing, stance])
            # Ensure exact length
            if len(result) != steps:
                result = np.resize(result, steps)
            return result
        
        def lift_pattern(steps):
            """Walking lift pattern - only lift during swing phase"""
            swing_steps = int(steps * 0.25)  # 25% of cycle in air
            stance_steps = steps - swing_steps
            
            # Only lift during swing phase
            lift = MovementPattern.lift(swing_steps, -self.clearance)
            ground = np.zeros(stance_steps)
            
            result = np.concatenate([lift, ground])
            # Ensure exact length
            if len(result) != steps:
                result = np.resize(result, steps)
            return result
        
        def hip_sway_pattern(steps, leg_side: str):
            """
            Hip sway for natural walking balance.
            
            Body sways toward the side with more supporting legs:
            - When left legs lift, body sways right for balance
            - When right legs lift, body sways left for balance
            """
            if leg_side == "left":
                # Left legs: body sways right when this leg is lifting
                # Create sway that peaks when leg is in air
                sway = np.zeros(steps)
                swing_start = 0
                swing_end = int(steps * 0.25)
                
                # During swing phase, body sways away from lifting leg
                if swing_end > swing_start:
                    sway[swing_start:swing_end] = np.sin(np.linspace(0, np.pi, swing_end - swing_start)) * self.hip_sway_amplitude
                
                # Add gentle overall sway pattern for natural movement
                overall_sway = np.sin(np.linspace(0, 2*np.pi, steps)) * (self.hip_sway_amplitude * 0.3)
                return sway + overall_sway
                
            else:  # right side
                # Right legs: body sways left when this leg is lifting  
                sway = np.zeros(steps)
                swing_start = 0
                swing_end = int(steps * 0.25)
                
                if swing_end > swing_start:
                    sway[swing_start:swing_end] = -np.sin(np.linspace(0, np.pi, swing_end - swing_start)) * self.hip_sway_amplitude
                
                overall_sway = -np.sin(np.linspace(0, 2*np.pi, steps)) * (self.hip_sway_amplitude * 0.3)
                return sway + overall_sway
        
        return {
            # Left side legs
            0: LegMovement(  # Left Front
                x=forward_stride, 
                y=lambda steps: hip_sway_pattern(steps, "left"),
                z=lift_pattern, 
                phase_shift=phase_shifts[0]
            ),
            2: LegMovement(  # Left Back  
                x=forward_stride,
                y=lambda steps: hip_sway_pattern(steps, "left"), 
                z=lift_pattern,
                phase_shift=phase_shifts[2]
            ),
            
            # Right side legs
            1: LegMovement(  # Right Front
                x=forward_stride,
                y=lambda steps: hip_sway_pattern(steps, "right"),
                z=lift_pattern, 
                phase_shift=phase_shifts[1]
            ),
            3: LegMovement(  # Right Back
                x=forward_stride,
                y=lambda steps: hip_sway_pattern(steps, "right"),
                z=lift_pattern,
                phase_shift=phase_shifts[3]
            ),
        }


if __name__ == "__main__":
    # Test the simplified system
    print("Testing Simplified Gait System")
    
    # Create a simple trot
    trot = SimpleTrot(stride=40, clearance=50, step_size=15)
    print(f"✓ SimpleTrot created - {len(trot.steps[0])} steps per leg")
    
    # Test iteration
    for i in range(5):
        pos = next(trot)
        print(f"Step {i}: Z-axis range: {pos[:, 2].min():.1f} to {pos[:, 2].max():.1f}")
    
    # Create trot with lateral
    lateral_trot = SimpleTrotWithLateral(stride=40, clearance=50, lateral_amplitude=6)
    print("✓ SimpleTrotWithLateral created")
    print(f"  Y-axis range: {lateral_trot.steps[0][:, 1].min():.1f} to {lateral_trot.steps[0][:, 1].max():.1f}")
    
    # Create turn gait
    turn_gait = SimpleTurn(stride=30, clearance=40, turn_direction=1)
    print("✓ SimpleTurn created")
    print(f"  Left legs Y-range: {turn_gait.steps[0][:, 1].min():.1f} to {turn_gait.steps[0][:, 1].max():.1f}")
    print(f"  Right legs Y-range: {turn_gait.steps[1][:, 1].min():.1f} to {turn_gait.steps[1][:, 1].max():.1f}")
    print("  (Opposite directions = efficient turning)")
    
    # Create walking gait
    walk_gait = SimpleWalk(stride=40, clearance=30, step_size=20, hip_sway_amplitude=10)
    print("✓ SimpleWalk created") 
    print(f"  Cycle length: {len(walk_gait.steps[0])} steps")
    print(f"  Hip sway range: {walk_gait.steps[0][:, 1].min():.1f} to {walk_gait.steps[0][:, 1].max():.1f} mm")
    print("  (Sequential leg movement with natural hip sway)")

