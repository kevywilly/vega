"""
Simplified Gait System - Production gaits for Vega robot

This module contains:
- MovementPattern: Reusable movement pattern building blocks
- LegMovement: Dataclass for leg movement definitions
- SimplifiedGait: Base class for declarative gait definitions
- SimpleTrotWithLateral: Production trot gait with hip sway
- SimpleSidestep: Production sidestep gait

For experimental gaits, see graveyard/gaits/experimental_gaits.py
"""

import numpy as np
from abc import abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Dict
from src.motion.gaits.gait import Gait
from src.motion.gaits.gait_params import GaitParams


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
    def trot_lateral_pattern(num_steps: int, amplitude: float = 1.0) -> np.ndarray:
        """Trot-specific hip sway pattern for natural movement"""
        return np.hstack([
            np.sin(np.linspace(0, np.pi, num_steps)) * 0.7,
            np.sin(np.linspace(np.pi, 2*np.pi, num_steps)) * 0.3,
            np.sin(np.linspace(0, np.pi, num_steps * 2)) * 0.2,
        ]) * amplitude

    @staticmethod
    def zero(steps: int) -> np.ndarray:
        """No movement"""
        return np.zeros(steps)


@dataclass
class LegMovement:
    """Define movement for a single axis of a leg"""
    x: Callable[[int], np.ndarray] | None = None  # Forward/back movement function
    y: Callable[[int], np.ndarray] | None = None  # Lateral movement function
    z: Callable[[int], np.ndarray] | None = None  # Up/down movement function
    phase_shift: int = 0  # Phase shift in steps


class SimplifiedGait(Gait):
    """
    Simplified gait that uses the proven Gait base class but allows
    declarative movement pattern definitions.
    """

    def build_steps(self):
        """Build steps using simplified movement definitions"""
        movements = self.define_leg_movements()
        total_steps = self.num_steps * 4

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

        # Apply phase shifts
        if leg1_movement.phase_shift > 0:
            x2 = np.roll(x2, leg1_movement.phase_shift)
            y2 = np.roll(y2, leg1_movement.phase_shift)
            z2 = np.roll(z2, leg1_movement.phase_shift)

        self.steps1 = Gait.reshape_steps(np.array([x1, y1, z1]), total_steps)
        self.steps2 = Gait.reshape_steps(np.array([x2, y2, z2]), total_steps)

    @abstractmethod
    def define_leg_movements(self) -> Dict[int, LegMovement]:
        """
        Define movement for leg groups.

        Return dict with:
        - 0: Movement for legs 0,2 (front-left, back-left)
        - 1: Movement for legs 1,3 (front-right, back-right)
        """
        pass


class SimpleTrotWithLateral(Gait):
    """
    Trot with lateral movement - PRODUCTION GAIT

    Used for FORWARD and BACKWARD movement in the controller.
    Properly inherits from the base Gait class.
    """

    def build_steps(self):
        # Forward/backward movement
        x = np.hstack([
            self.stride_forward(),
            self.stride_home(),
            self.stride_back(self.num_steps * 2),
        ]) * int(self.stride)

        # Lateral movement using trot pattern
        y = MovementPattern.trot_lateral_pattern(self.num_steps, self.hip_sway)

        # Vertical movement
        z = np.hstack([
            self.downupdown(),
            np.repeat(self.zeros, 3),
        ]) * (-self.clearance)

        # Build step sequences
        self.steps1 = Gait.reshape_steps(np.array([x, y, z]), self.num_steps * 4)

        # Phase shift for diagonal gait pattern, opposite lateral movement
        steps2_x = np.roll(x, self.num_steps * 2)
        steps2_y = -np.roll(y, self.num_steps * 2)
        steps2_z = np.roll(z, self.num_steps * 2)

        self.steps2 = Gait.reshape_steps(np.array([steps2_x, steps2_y, steps2_z]), self.num_steps * 4)


class SimpleSidestep(SimplifiedGait):
    """
    Sidestep gait - PRODUCTION GAIT

    Used for LEFT and RIGHT movement in the controller.
    """

    def define_leg_movements(self) -> Dict[int, LegMovement]:
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
