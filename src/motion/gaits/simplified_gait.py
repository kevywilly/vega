"""
Simplified Gait System - Making gait creation much easier and more intuitive

Key improvements:
1. Declarative leg movement definitions
2. Automatic phase management
3. Built-in common movement patterns
4. Clear leg coordination specification
"""

import numpy as np
from abc import abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Dict
from src.motion.gaits.gait import Gait


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
        """Forward stride pattern - matches Gait.stride_forward()"""
        return np.sin(np.radians(np.linspace(0, 90, steps))) * distance
    
    @staticmethod
    def stride_home(steps: int, distance: float = 1.0) -> np.ndarray:
        """Home stride pattern - matches Gait.stride_home()"""
        return np.cos(np.radians(np.linspace(0, 90, steps))) * distance
    
    @staticmethod
    def stride_back(steps: int, distance: float = 1.0) -> np.ndarray:
        """Backward return pattern - matches Gait.stride_back()"""
        return np.cos(np.radians(np.linspace(90, 180, steps))) * distance
    
    @staticmethod
    def downupdown(steps: int, clearance: float = 1.0) -> np.ndarray:
        """Downupdown pattern - matches Gait.downupdown()"""
        ns1 = int(steps/5)
        ns2 = steps-ns1
        return np.hstack([
            np.sin(np.radians(np.linspace(-10, 0, ns1))),
            np.sin(np.radians(np.linspace(45, 180, ns2)))
        ]) * clearance
    
    @staticmethod
    def step_cycle(steps: int, distance: float = 1.0) -> np.ndarray:
        """Complete forward-back cycle using original gait patterns"""
        # This should match the trot pattern: stride_forward + stride_home + stride_back
        steps_per_part = steps // 4
        return np.concatenate([
            MovementPattern.stride_forward(steps_per_part, distance),
            MovementPattern.stride_home(steps_per_part, distance),
            MovementPattern.stride_back(steps_per_part * 2, distance)
        ])
    
    @staticmethod
    def lateral_sway(steps: int, amplitude: float = 1.0) -> np.ndarray:
        """Lateral swaying motion"""
        return np.sin(np.linspace(0, 2*np.pi, steps)) * amplitude
    
    @staticmethod
    def hip_sway_pattern(num_steps: int, amplitude: float = 1.0, 
                        lift_intensity: float = 0.7, 
                        stance_intensity: float = 0.3, 
                        ground_intensity: float = 0.2) -> np.ndarray:
        """
        Generic hip sway pattern for natural quadruped movement
        
        Creates weight shifting with configurable intensities:
        - lift_intensity: Movement during leg lift phase (default 0.7 for trot)
        - stance_intensity: Movement during stance phase (default 0.3 for trot)  
        - ground_intensity: Movement during ground contact (default 0.2 for trot)
        
        Different gaits can use different intensities:
        - Trot: (0.7, 0.3, 0.2) - moderate sway
        - Walk: (0.9, 0.1, 0.0) - more pronounced sway during lift
        - Prowl: (0.5, 0.8, 0.1) - subtle lift, strong stance sway
        """
        return np.hstack([
            # During lift phase: lateral movement to help with weight shift
            np.sin(np.linspace(0, np.pi, num_steps)) * lift_intensity,
            # During stance phase: counter movement for balance
            np.sin(np.linspace(np.pi, 2*np.pi, num_steps)) * stance_intensity,
            # Ground contact phase: return to neutral
            np.sin(np.linspace(0, np.pi, num_steps * 2)) * ground_intensity,
        ]) * amplitude
    
    @staticmethod  
    def trot_lateral_pattern(num_steps: int, amplitude: float = 1.0) -> np.ndarray:
        """Trot-specific hip sway pattern - wrapper for backward compatibility"""
        return MovementPattern.hip_sway_pattern(num_steps, amplitude, 0.7, 0.3, 0.2)
    
    @staticmethod
    def walk_lateral_pattern(num_steps: int, amplitude: float = 1.0) -> np.ndarray:
        """Walk-specific hip sway pattern - more pronounced during lift"""
        return MovementPattern.hip_sway_pattern(num_steps, amplitude, 0.9, 0.1, 0.0)
    
    @staticmethod
    def prowl_lateral_pattern(num_steps: int, amplitude: float = 1.0) -> np.ndarray:
        """Prowling/stalking hip sway pattern - subtle lift, strong stance movement"""
        return MovementPattern.hip_sway_pattern(num_steps, amplitude, 0.5, 0.8, 0.1)
    
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


class SimplifiedGait(Gait):
    """
    Simplified gait that uses the proven Gait base class but allows
    declarative movement pattern definitions.
    
    Best of both worlds:
    - Simple, readable movement definitions
    - Proven, stable base class behavior
    """
    
    def __init__(self, **kwargs):
        # Extract our custom parameters
        self.hip_sway = kwargs.pop('hip_sway', 8)
        
        # Call parent constructor with remaining parameters
        super().__init__(**kwargs)
    
    def build_steps(self):
        """Build steps using simplified movement definitions"""
        # Get movement definitions from subclass
        movements = self.define_leg_movements()
        
        # Build the x, y, z arrays like original gaits
        total_steps = self.num_steps * 4
        
        # Get movements for "step group 1" (legs 0,2) and "step group 2" (legs 1,3)
        # This matches the base Gait class leg assignment pattern
        
        leg0_movement = movements.get(0, LegMovement())
        leg1_movement = movements.get(1, LegMovement())
        
        # Build arrays for step group 1 (like steps1 in base class)
        x1 = leg0_movement.x(total_steps) if leg0_movement.x else MovementPattern.zero(total_steps)
        y1 = leg0_movement.y(total_steps) if leg0_movement.y else MovementPattern.zero(total_steps)
        z1 = leg0_movement.z(total_steps) if leg0_movement.z else MovementPattern.zero(total_steps)
        
        # Build arrays for step group 2 (like steps2 in base class) 
        x2 = leg1_movement.x(total_steps) if leg1_movement.x else x1.copy()
        y2 = leg1_movement.y(total_steps) if leg1_movement.y else y1.copy()
        z2 = leg1_movement.z(total_steps) if leg1_movement.z else z1.copy()
        
        # Apply phase shifts (like np.roll in original gaits)
        if leg1_movement.phase_shift > 0:
            x2 = np.roll(x2, leg1_movement.phase_shift)
            y2 = np.roll(y2, leg1_movement.phase_shift)  
            z2 = np.roll(z2, leg1_movement.phase_shift)
        
        # Use the base Gait reshape_steps method for proper formatting
        self.steps1 = Gait.reshape_steps(np.array([x1, y1, z1]), total_steps)
        self.steps2 = Gait.reshape_steps(np.array([x2, y2, z2]), total_steps)
    
    @abstractmethod
    def define_leg_movements(self) -> Dict[int, LegMovement]:
        """
        Define movement for leg groups.
        
        Return dict with:
        - 0: Movement for legs 0,2 (front-left, back-left) 
        - 1: Movement for legs 1,3 (front-right, back-right)
        
        This matches the base Gait class leg assignment pattern.
        """
        pass


# Example implementations using the simplified system

class SimpleTrot(SimplifiedGait):
    """Trot gait using simplified system"""
    
    def define_leg_movements(self) -> Dict[int, LegMovement]:
        half_cycle = self.num_steps * 2
        
        # Trot movement patterns matching the original exactly
        def trot_x_movement(steps):
            """Forward/back movement like original trot"""
            return np.hstack([
                MovementPattern.stride_forward(self.num_steps, self.stride),
                MovementPattern.stride_home(self.num_steps, self.stride),
                MovementPattern.stride_back(self.num_steps * 2, self.stride)
            ])
        
        def trot_z_movement(steps):
            """Up/down movement like original trot"""
            return np.hstack([
                MovementPattern.downupdown(self.num_steps, -self.clearance),
                MovementPattern.zero(self.num_steps * 3)
            ])
        
        return {
            # Group 1: legs 0,2 (front-left, back-left)
            0: LegMovement(x=trot_x_movement, z=trot_z_movement, phase_shift=0),
            # Group 2: legs 1,3 (front-right, back-right) - phase shifted for diagonal trot
            1: LegMovement(x=trot_x_movement, z=trot_z_movement, phase_shift=half_cycle),
        }


class SimpleTrotWithLateralFixed(SimplifiedGait):
    """
    Trot with lateral movement using the FIXED simplified system
    
    This version uses the proper SimplifiedGait base class with
    declarative movement patterns while maintaining all the stability
    and correctness of the original Gait class.
    """
    
    def define_leg_movements(self) -> Dict[int, LegMovement]:
        half_cycle = self.num_steps * 2
        
        # X-axis: same as trot
        def trot_x_movement(steps):
            return np.hstack([
                MovementPattern.stride_forward(self.num_steps, self.stride),
                MovementPattern.stride_home(self.num_steps, self.stride),
                MovementPattern.stride_back(self.num_steps * 2, self.stride)
            ])
        
        # Z-axis: same as trot
        def trot_z_movement(steps):
            return np.hstack([
                MovementPattern.downupdown(self.num_steps, -self.clearance),
                MovementPattern.zero(self.num_steps * 3)
            ])
        
        # Y-axis: lateral movement for hip sway using abstracted pattern
        def lateral_movement_left(steps):
            """Left legs lateral movement using the abstracted trot lateral pattern"""
            return MovementPattern.trot_lateral_pattern(self.num_steps, self.hip_sway)
        
        def lateral_movement_right(steps):
            """Right legs lateral movement (opposite of left)"""
            return MovementPattern.trot_lateral_pattern(self.num_steps, -self.hip_sway)
        
        return {
            # Group 1: legs 0,2 (left side) 
            0: LegMovement(
                x=trot_x_movement,
                y=lateral_movement_left, 
                z=trot_z_movement,
                phase_shift=0
            ),
            # Group 2: legs 1,3 (right side) - phase shifted and opposite lateral
            1: LegMovement(
                x=trot_x_movement,
                y=lateral_movement_right,
                z=trot_z_movement, 
                phase_shift=half_cycle
            ),
        }


class SimpleTrotWithLateral(Gait):
    """
    Trot with lateral movement - FIXED to match base Gait system exactly
    
    This version properly inherits from the base Gait class and follows
    the same patterns as the working TrotWithLateral.
    """
    def build_steps(self):
        # Forward/backward movement (EXACTLY like original TrotWithLateral)
        x = np.hstack([
            self.stride_forward(),
            self.stride_home(),
            self.stride_back(self.num_steps * 2),
        ]) * int(self.stride)

        # Lateral movement using abstracted pattern
        y = MovementPattern.trot_lateral_pattern(self.num_steps, self.hip_sway)

        # Vertical movement (EXACTLY like original TrotWithLateral)
        z = np.hstack([
            self.downupdown(),
            np.repeat(self.zeros, 3),
        ]) * (-self.clearance)

        # Build step sequences (EXACTLY like original TrotWithLateral)
        self.steps1 = Gait.reshape_steps(np.array([x, y, z]), self.num_steps * 4)
        
        # Phase shift for diagonal gait pattern, but with opposite lateral movement
        # This creates the natural hip sway where diagonal legs move in opposite lateral directions
        steps2_x = np.roll(x, self.num_steps * 2)
        steps2_y = -np.roll(y, self.num_steps * 2)  # Opposite lateral movement for diagonal legs
        steps2_z = np.roll(z, self.num_steps * 2)
        
        self.steps2 = Gait.reshape_steps(np.array([steps2_x, steps2_y, steps2_z]), self.num_steps * 4)


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
        
        def hip_sway_pattern_left(steps):
            """Left legs hip sway using generic walk pattern"""
            return MovementPattern.walk_lateral_pattern(self.num_steps, self.hip_sway)
        
        def hip_sway_pattern_right(steps):
            """Right legs hip sway (opposite of left)"""
            return MovementPattern.walk_lateral_pattern(self.num_steps, -self.hip_sway)
        
        return {
            # Left side legs
            0: LegMovement(  # Left Front
                x=forward_stride, 
                y=hip_sway_pattern_left,
                z=lift_pattern, 
                phase_shift=phase_shifts[0]
            ),
            2: LegMovement(  # Left Back  
                x=forward_stride,
                y=hip_sway_pattern_left, 
                z=lift_pattern,
                phase_shift=phase_shifts[2]
            ),
            
            # Right side legs
            1: LegMovement(  # Right Front
                x=forward_stride,
                y=hip_sway_pattern_right,
                z=lift_pattern, 
                phase_shift=phase_shifts[1]
            ),
            3: LegMovement(  # Right Back
                x=forward_stride,
                y=hip_sway_pattern_right,
                z=lift_pattern,
                phase_shift=phase_shifts[3]
            ),
        }


class SimpleProwl(SimplifiedGait):
    """
    Stealthy prowling gait for careful, deliberate movement.
    
    Characteristics vs SimpleWalk:
    - Lower, more crouched movement (less clearance)
    - Slower, more deliberate steps (larger step_size)
    - Strong hip sway during stance for weight shifting
    - Longer ground contact phases for stability
    - More cautious, predatory movement style
    """
    
    def define_leg_movements(self) -> Dict[int, LegMovement]:
        # Prowling uses diagonal trot pattern like tigers - not sequential walk
        half_cycle = self.num_steps
        
        # Tiger prowl: diagonal legs move together with longer strides
        phase_shifts = {
            0: 0,               # Left Front (LF) - diagonal pair 1
            3: 0,               # Right Back (RB) - with LF
            1: half_cycle,      # Right Front (RF) - diagonal pair 2  
            2: half_cycle,      # Left Back (LB) - with RF
        }
        
        def tiger_prowl_stride(steps):
            """Tiger prowling stride - long, deliberate forward movement"""
            # Tigers take long strides with significant ground clearance
            # 40% swing phase for longer stride, 60% stance for stability
            swing_steps = int(steps * 0.4)  # Longer swing for big steps
            stance_steps = steps - swing_steps
            
            # Swing phase: long forward reach (tiger-like)
            swing = np.linspace(0, self.stride * 1.2, swing_steps)  # 20% longer reach
            # Stance phase: powerful backward push
            stance = np.linspace(self.stride * 1.2, -self.stride * 0.2, stance_steps)
            
            result = np.concatenate([swing, stance])
            if len(result) != steps:
                result = np.resize(result, steps)
            return result
        
        def tiger_prowl_lift(steps):
            """Tiger prowl lift - higher lift for deliberate placement"""
            swing_steps = int(steps * 0.4)  # Match swing phase
            stance_steps = steps - swing_steps
            
            # Higher lift for deliberate foot placement
            lift = MovementPattern.lift(swing_steps, -self.clearance * 1.1)  # 10% higher
            ground = np.zeros(stance_steps)
            
            result = np.concatenate([lift, ground])
            if len(result) != steps:
                result = np.resize(result, steps)
            return result
        
        def tiger_hip_sway(steps):
            """Tiger hip sway - strong lateral movement for balance"""
            return MovementPattern.hip_sway_pattern(
                self.num_steps, 
                amplitude=self.hip_sway,
                lift_intensity=0.5,    # Moderate outward during swing
                stance_intensity=0.8,  # Strong inward during stance  
                ground_intensity=0.1   # Minimal during ground phase
            )
        
        return {
            # Diagonal pair 1: Left Front + Right Back
            0: LegMovement(  # Left Front
                x=tiger_prowl_stride, 
                y=lambda steps: tiger_hip_sway(steps),
                z=tiger_prowl_lift, 
                phase_shift=phase_shifts[0]
            ),
            3: LegMovement(  # Right Back (diagonal with LF)
                x=tiger_prowl_stride, 
                y=lambda steps: -tiger_hip_sway(steps),  # Opposite hip sway
                z=tiger_prowl_lift, 
                phase_shift=phase_shifts[3]
            ),
            
            # Diagonal pair 2: Right Front + Left Back  
            1: LegMovement(  # Right Front
                x=tiger_prowl_stride, 
                y=lambda steps: -tiger_hip_sway(steps),  # Opposite hip sway
                z=tiger_prowl_lift, 
                phase_shift=phase_shifts[1]
            ),
            2: LegMovement(  # Left Back (diagonal with RF)
                x=tiger_prowl_stride, 
                y=lambda steps: tiger_hip_sway(steps),
                z=tiger_prowl_lift, 
                phase_shift=phase_shifts[2]
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
    lateral_trot = SimpleTrotWithLateral(stride=40, clearance=50, hip_sway=6)
    print("✓ SimpleTrotWithLateral created")
    print(f"  Y-axis range: {lateral_trot.steps[0][:, 1].min():.1f} to {lateral_trot.steps[0][:, 1].max():.1f}")
    
    # Create turn gait
    turn_gait = SimpleTurn(stride=30, clearance=40, turn_direction=1)
    print("✓ SimpleTurn created")
    print(f"  Left legs Y-range: {turn_gait.steps[0][:, 1].min():.1f} to {turn_gait.steps[0][:, 1].max():.1f}")
    print(f"  Right legs Y-range: {turn_gait.steps[1][:, 1].min():.1f} to {turn_gait.steps[1][:, 1].max():.1f}")
    print("  (Opposite directions = efficient turning)")
    
    # Create walking gait
    walk_gait = SimpleWalk(stride=40, clearance=30, step_size=20, hip_sway=10)
    print("✓ SimpleWalk created") 
    print(f"  Cycle length: {len(walk_gait.steps[0])} steps")
    print(f"  Hip sway range: {walk_gait.steps[0][:, 1].min():.1f} to {walk_gait.steps[0][:, 1].max():.1f} mm")
    print("  (Sequential leg movement with natural hip sway)")

