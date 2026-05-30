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
from src.motion.gaits.gait_spec import GaitSpec, LegSpec, compile_spec
from src.motion.gaits import trajectories as T


class LegPhase(Enum):
    """Define common leg groupings for gaits"""
    ALL = "all"           # All legs together (jump)
    DIAGONAL = "diagonal"  # Diagonal pairs (trot)
    LATERAL = "lateral"    # Left/right pairs (pace)
    SEQUENTIAL = "sequential"  # One leg at a time (walk)


class MovementPattern:
    """Pre-built movement patterns (scaled wrappers over the trajectories.py shape
    library -- the single source of trajectory math). Retained for the legacy
    declarative path and tests; new gaits should reference trajectories directly
    via GaitSpec."""

    @staticmethod
    def lift(steps: int, height: float = 1.0) -> np.ndarray:
        return T.lift(steps) * height

    @staticmethod
    def stride_forward(steps: int, distance: float = 1.0) -> np.ndarray:
        return T.stride_forward(steps) * distance

    @staticmethod
    def stride_home(steps: int, distance: float = 1.0) -> np.ndarray:
        return T.stride_home(steps) * distance

    @staticmethod
    def stride_back(steps: int, distance: float = 1.0) -> np.ndarray:
        return T.stride_back(steps) * distance

    @staticmethod
    def downupdown(steps: int, clearance: float = 1.0) -> np.ndarray:
        return T.downupdown(steps) * clearance

    @staticmethod
    def step_cycle(steps: int, distance: float = 1.0) -> np.ndarray:
        return T.step_cycle(steps) * distance

    @staticmethod
    def lateral_sway(steps: int, amplitude: float = 1.0) -> np.ndarray:
        return T.lateral_sway(steps) * amplitude

    @staticmethod
    def trot_lateral_pattern(num_steps: int, amplitude: float = 1.0) -> np.ndarray:
        return T.trot_lateral_pattern(num_steps) * amplitude

    @staticmethod
    def zero(steps: int) -> np.ndarray:
        return T.zero(steps)


@dataclass
class LegMovement:
    """DEPRECATED -- superseded by gait_spec.LegSpec. Define movement for a single
    axis of a leg. Retained only for the legacy SimplifiedGait path; new gaits use
    GaitSpec/LegSpec."""
    x: Callable[[int], np.ndarray] | None = None  # Forward/back movement function
    y: Callable[[int], np.ndarray] | None = None  # Lateral movement function
    z: Callable[[int], np.ndarray] | None = None  # Up/down movement function
    phase_shift: int = 0  # Phase shift in steps


class SimplifiedGait(Gait):
    """
    DEPRECATED -- superseded by GaitSpec + compile_spec (gait_spec.py).

    This declarative base only ever read legs 0 and 1 and welded the rest into
    diagonal pairs, so a 4-independent-leg gait was inexpressible through it (the
    ceiling the refactor removed). It has no production subclasses anymore --
    trot/sidestep/turn build via GaitSpec, and prowl is the last imperative
    holdout pending its rebuild (plan item 4). Kept for reference / graveyard
    experiments only; do not author new gaits here.
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

    Used for FORWARD and BACKWARD movement in the controller. Expressed
    declaratively via GaitSpec: diagonal pairs {0,2} and {1,3} run a half-cycle
    apart, with the lateral (y) hip-sway negated on the second pair -- the
    deliberate compensation for the unmirrored coxa, kept in the gait layer.
    See docs/plans/2026-05-30-001-refactor-gait-core-phasing-plan.md.
    """

    def build_steps(self):
        self.steps = compile_spec(self._spec())

    def _spec(self) -> GaitSpec:
        num = self.num_steps
        stride, clearance, hip_sway = int(self.stride), self.clearance, self.hip_sway

        def x(_n):
            return np.hstack([
                T.stride_forward(num), T.stride_home(num), T.stride_back(num * 2),
            ]) * stride

        def y(_n):
            return T.trot_lateral_pattern(num) * hip_sway

        def z(_n):
            return np.hstack([T.downupdown(num), T.zero(num * 3)]) * (-clearance)

        a = LegSpec(x=x, y=y, z=z, phase_offset=0.0)                 # legs 0, 2
        b = LegSpec(x=x, y=lambda n: -y(n), z=z, phase_offset=0.5)   # legs 1, 3: -y
        return GaitSpec(period=num * 4, duty_factor=0.75, legs=[a, b, a, b])


class SimpleSidestep(Gait):
    """
    Sidestep gait - PRODUCTION GAIT (LEFT / RIGHT).

    Diagonal pairs {0,2} and {1,3} step laterally a quarter-cycle apart, built via
    GaitSpec. LEFT vs RIGHT is the sign of the stride (is_reversed), exactly as
    before.

    NOTE: this preserves the *realized* legacy behavior. The old define_leg_movements
    dict nominally placed legs 2,3 at their own phases, but the previous
    SimplifiedGait.build_steps only read legs 0,1 and welded the rest -- so legs 2,3
    actually mirrored 0,1 (the diagonal weld). That is what runs today and what is
    reproduced here. Honoring the dict's 4 distinct phases would be a behavior change,
    deferred -- not part of this behavior-preserving refactor.
    """

    def build_steps(self):
        self.steps = compile_spec(self._spec())

    def _spec(self) -> GaitSpec:
        num = self.num_steps
        stride, clearance = self.stride, self.clearance

        def y(_n):
            return T.step_cycle(num * 4) * stride

        def z(_n):
            pattern = np.zeros(num * 4)
            pattern[:num] = T.lift(num) * (-clearance)
            return pattern

        a = LegSpec(y=y, z=z, phase_offset=0.0)    # legs 0, 2
        b = LegSpec(y=y, z=z, phase_offset=0.25)   # legs 1, 3 (quarter-cycle)
        return GaitSpec(period=num * 4, duty_factor=0.75, legs=[a, b, a, b])
