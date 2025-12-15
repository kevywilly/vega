"""
Experimental Gait Implementations - Preserved for future reference

These gaits were developed but not deployed to production.
To use any of these, move them back to src/motion/gaits/simplified_gait.py
"""

import numpy as np
from typing import Dict

# Note: These classes depend on:
# - SimplifiedGait base class from src/motion/gaits/simplified_gait.py
# - MovementPattern class from src/motion/gaits/simplified_gait.py
# - LegMovement dataclass from src/motion/gaits/simplified_gait.py
# - Gait base class from src/motion/gaits/gait.py

# To restore, add this import:
# from src.motion.gaits.simplified_gait import SimplifiedGait, MovementPattern, LegMovement


class SimpleTrot:
    """Trot gait using simplified system - UNUSED (production uses SimpleTrotWithLateral)"""

    def define_leg_movements(self) -> Dict:
        half_cycle = self.num_steps * 2

        def trot_x_movement(steps):
            """Forward/back movement like original trot"""
            return np.hstack([
                np.sin(np.radians(np.linspace(0, 90, self.num_steps))) * self.stride,
                np.cos(np.radians(np.linspace(0, 90, self.num_steps))) * self.stride,
                np.cos(np.radians(np.linspace(90, 180, self.num_steps * 2))) * self.stride
            ])

        def trot_z_movement(steps):
            """Up/down movement like original trot"""
            ns1 = int(self.num_steps/5)
            ns2 = self.num_steps-ns1
            downupdown = np.hstack([
                np.sin(np.radians(np.linspace(-10, 0, ns1))),
                np.sin(np.radians(np.linspace(45, 180, ns2)))
            ])
            return np.hstack([
                downupdown * -self.clearance,
                np.zeros(self.num_steps * 3)
            ])

        # Requires LegMovement dataclass
        return {
            0: {'x': trot_x_movement, 'z': trot_z_movement, 'phase_shift': 0},
            1: {'x': trot_x_movement, 'z': trot_z_movement, 'phase_shift': half_cycle},
        }


class SimpleTrotWithLateralFixed:
    """
    Trot with lateral movement using the FIXED simplified system

    This version uses the proper SimplifiedGait base class with
    declarative movement patterns. UNUSED in production.
    """

    def define_leg_movements(self) -> Dict:
        half_cycle = self.num_steps * 2

        def trot_x_movement(steps):
            return np.hstack([
                np.sin(np.radians(np.linspace(0, 90, self.num_steps))) * self.stride,
                np.cos(np.radians(np.linspace(0, 90, self.num_steps))) * self.stride,
                np.cos(np.radians(np.linspace(90, 180, self.num_steps * 2))) * self.stride
            ])

        def trot_z_movement(steps):
            ns1 = int(self.num_steps/5)
            ns2 = self.num_steps-ns1
            downupdown = np.hstack([
                np.sin(np.radians(np.linspace(-10, 0, ns1))),
                np.sin(np.radians(np.linspace(45, 180, ns2)))
            ])
            return np.hstack([
                downupdown * -self.clearance,
                np.zeros(self.num_steps * 3)
            ])

        def lateral_movement_left(steps):
            return np.hstack([
                np.sin(np.linspace(0, np.pi, self.num_steps)) * 0.7,
                np.sin(np.linspace(np.pi, 2*np.pi, self.num_steps)) * 0.3,
                np.sin(np.linspace(0, np.pi, self.num_steps * 2)) * 0.2,
            ]) * self.hip_sway

        def lateral_movement_right(steps):
            return np.hstack([
                np.sin(np.linspace(0, np.pi, self.num_steps)) * 0.7,
                np.sin(np.linspace(np.pi, 2*np.pi, self.num_steps)) * 0.3,
                np.sin(np.linspace(0, np.pi, self.num_steps * 2)) * 0.2,
            ]) * -self.hip_sway

        return {
            0: {'x': trot_x_movement, 'y': lateral_movement_left, 'z': trot_z_movement, 'phase_shift': 0},
            1: {'x': trot_x_movement, 'y': lateral_movement_right, 'z': trot_z_movement, 'phase_shift': half_cycle},
        }


class SimpleJump:
    """Jump gait - all legs together. UNUSED."""

    def define_leg_movements(self) -> Dict:
        def jump_up_down(steps):
            half_steps = steps // 2
            up = np.sin(np.linspace(0, np.pi, half_steps)) * self.clearance
            down = np.sin(np.linspace(0, np.pi, half_steps)) * -self.clearance
            return np.concatenate([up, down])

        movement = {'z': jump_up_down}
        return {0: movement, 1: movement, 2: movement, 3: movement}


class SimpleTurn:
    """
    Simplified in-place turning gait. UNUSED in production (turn.py is used instead).

    Much cleaner than the existing Turn implementation:
    - Uses diagonal leg coordination (like trot)
    - Left legs step one direction, right legs step opposite
    - Creates efficient rotation around robot center
    """

    def __init__(self, turn_direction: int = 1, **kwargs):
        self.turn_direction = turn_direction
        # Note: Would need to call super().__init__(**kwargs)

    def define_leg_movements(self) -> Dict:
        half_cycle = self.num_steps

        def step_cycle(steps, distance):
            steps_per_part = steps // 4
            return np.concatenate([
                np.sin(np.radians(np.linspace(0, 90, steps_per_part))) * distance,
                np.cos(np.radians(np.linspace(0, 90, steps_per_part))) * distance,
                np.cos(np.radians(np.linspace(90, 180, steps_per_part * 2))) * distance
            ])

        def left_turn_step(steps):
            return step_cycle(steps, self.stride * self.turn_direction)

        def right_turn_step(steps):
            return step_cycle(steps, -self.stride * self.turn_direction)

        def lift_pattern(steps):
            pattern = np.zeros(steps)
            lift_steps = self.num_steps
            pattern[:lift_steps] = np.sin(np.linspace(0, np.pi, lift_steps)) * -self.clearance
            return pattern

        return {
            0: {'y': left_turn_step, 'z': lift_pattern, 'phase_shift': 0},
            2: {'y': left_turn_step, 'z': lift_pattern, 'phase_shift': half_cycle},
            1: {'y': right_turn_step, 'z': lift_pattern, 'phase_shift': half_cycle},
            3: {'y': right_turn_step, 'z': lift_pattern, 'phase_shift': 0},
        }


class SimpleWalk:
    """
    Natural walking gait with sequential leg movement and hip sway.
    UNUSED in production.

    Mimics natural quadruped walking like tigers/cats:
    - Sequential leg lifting (one at a time)
    - Hip sway for balance and natural movement
    - Longer ground contact phases for stability
    """

    def define_leg_movements(self) -> Dict:
        cycle_steps = self.num_steps * 4
        quarter_cycle = self.num_steps

        phase_shifts = {
            0: 0,
            1: quarter_cycle,
            2: quarter_cycle * 2,
            3: quarter_cycle * 3,
        }

        def front_leg_stride(steps):
            swing_steps = int(steps * 0.3)
            stance_steps = steps - swing_steps
            swing = np.linspace(0, self.stride * 1.1, swing_steps)
            stance = np.linspace(self.stride * 1.1, -self.stride * 0.1, stance_steps)
            result = np.concatenate([swing, stance])
            if len(result) != steps:
                result = np.resize(result, steps)
            return result

        def hind_leg_stride(steps):
            swing_steps = int(steps * 0.3)
            stance_steps = steps - swing_steps
            swing = np.linspace(0, self.stride * 0.8, swing_steps)
            stance = np.linspace(self.stride * 0.8, -self.stride * 0.4, stance_steps)
            result = np.concatenate([swing, stance])
            if len(result) != steps:
                result = np.resize(result, steps)
            return result

        def cat_lift_pattern(steps):
            swing_steps = int(steps * 0.3)
            stance_steps = steps - swing_steps
            high_lift = np.sin(np.linspace(0, np.pi, swing_steps)) * -self.clearance * 1.1
            ground = np.zeros(stance_steps)
            result = np.concatenate([high_lift, ground])
            if len(result) != steps:
                result = np.resize(result, steps)
            return result

        def hip_sway_left(steps):
            return np.hstack([
                np.sin(np.linspace(0, np.pi, self.num_steps)) * 0.3,
                np.sin(np.linspace(np.pi, 2*np.pi, self.num_steps)) * 0.7,
                np.sin(np.linspace(0, np.pi, self.num_steps * 2)) * 0.1,
            ]) * self.hip_sway * 0.6

        def hip_sway_right(steps):
            return hip_sway_left(steps) * -1

        return {
            0: {'x': front_leg_stride, 'y': hip_sway_left, 'z': cat_lift_pattern, 'phase_shift': phase_shifts[0]},
            1: {'x': front_leg_stride, 'y': hip_sway_right, 'z': cat_lift_pattern, 'phase_shift': phase_shifts[1]},
            2: {'x': hind_leg_stride, 'y': hip_sway_left, 'z': cat_lift_pattern, 'phase_shift': phase_shifts[2]},
            3: {'x': hind_leg_stride, 'y': hip_sway_right, 'z': cat_lift_pattern, 'phase_shift': phase_shifts[3]},
        }


class SimpleProwl:
    """
    Stealthy prowling gait for careful, deliberate movement.
    UNUSED in production.

    Characteristics vs SimpleWalk:
    - Lower, more crouched movement (less clearance)
    - Slower, more deliberate steps
    - Strong hip sway during stance for weight shifting
    """

    def define_leg_movements(self) -> Dict:
        half_cycle = self.num_steps

        phase_shifts = {
            0: 0,
            3: 0,
            1: half_cycle,
            2: half_cycle,
        }

        def tiger_prowl_stride(steps):
            swing_steps = int(steps * 0.4)
            stance_steps = steps - swing_steps
            swing = np.linspace(0, self.stride * 1.2, swing_steps)
            stance = np.linspace(self.stride * 1.2, -self.stride * 0.2, stance_steps)
            result = np.concatenate([swing, stance])
            if len(result) != steps:
                result = np.resize(result, steps)
            return result

        def tiger_prowl_lift(steps):
            swing_steps = int(steps * 0.4)
            stance_steps = steps - swing_steps
            lift = np.sin(np.linspace(0, np.pi, swing_steps)) * -self.clearance * 1.1
            ground = np.zeros(stance_steps)
            result = np.concatenate([lift, ground])
            if len(result) != steps:
                result = np.resize(result, steps)
            return result

        def tiger_hip_sway(steps):
            return np.hstack([
                np.sin(np.linspace(0, np.pi, self.num_steps)) * 0.5,
                np.sin(np.linspace(np.pi, 2*np.pi, self.num_steps)) * 0.8,
                np.sin(np.linspace(0, np.pi, self.num_steps * 2)) * 0.1,
            ]) * self.hip_sway

        return {
            0: {'x': tiger_prowl_stride, 'y': tiger_hip_sway, 'z': tiger_prowl_lift, 'phase_shift': phase_shifts[0]},
            3: {'x': tiger_prowl_stride, 'y': lambda s: -tiger_hip_sway(s), 'z': tiger_prowl_lift, 'phase_shift': phase_shifts[3]},
            1: {'x': tiger_prowl_stride, 'y': lambda s: -tiger_hip_sway(s), 'z': tiger_prowl_lift, 'phase_shift': phase_shifts[1]},
            2: {'x': tiger_prowl_stride, 'y': tiger_hip_sway, 'z': tiger_prowl_lift, 'phase_shift': phase_shifts[2]},
        }
