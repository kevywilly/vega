"""
Declarative gait specification.

A `GaitSpec` is the data model for a gait in the new core: a cycle period (in
ticks), a duty factor, and one `LegSpec` per leg describing that leg's phase
offset and foot trajectory. It separates gait TIMING (period, duty factor,
phase offsets) from foot TRAJECTORY SHAPE (the per-leg x/y/z pattern functions),
mirroring the MIT Cheetah / Stanford Pupper gait-scheduler model.

This module defines the schema only. Compiling a `GaitSpec` into the
`(4, N, 3)` step array consumed by the iterator lives in `compile_spec` (added in
plan unit U3); nothing here constructs motion or touches NumPy state.

See docs/plans/2026-05-30-001-refactor-gait-core-phasing-plan.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

import numpy as np

# A trajectory function maps a step count N to an (N,) array of offsets in mm for
# one axis over the full cycle. Mirrors the `Callable[[int], np.ndarray]` shape of
# the existing LegMovement fields in simplified_gait.py.
TrajectoryFn = Callable[[int], np.ndarray]


@dataclass
class LegSpec:
    """Declarative spec for a single leg over one full gait cycle.

    phase_offset: where this leg's cycle starts relative to global phase, in [0, 1)
                  (0.5 = half-cycle behind; the diagonal-trot offset). Values
                  outside [0, 1) are accepted and wrapped by the phase utilities.
    x, y, z:      per-axis trajectory functions (mm), each `N -> (N,)`. A None axis
                  means "no motion on this axis" (the compiler treats it as zeros).
                  The deliberate lateral y-sign flip is expressed by a leg declaring
                  the negation of its pair's y function -- it is gait-layer data,
                  never kinematics.
    """

    phase_offset: float = 0.0
    x: Optional[TrajectoryFn] = None
    y: Optional[TrajectoryFn] = None
    z: Optional[TrajectoryFn] = None


@dataclass
class GaitSpec:
    """A full gait: cycle period in ticks, duty factor, and exactly 4 leg specs.

    legs is indexed by leg id (0=front-left, 1=front-right, 2=back-right,
    3=back-left), matching the codebase leg numbering. duty_factor is the stance
    fraction beta in (0, 1] (e.g. ~0.75 for the current gaits, >0.75 for a
    statically stable wave gait).
    """

    period: int
    duty_factor: float
    legs: List[LegSpec]

    def __post_init__(self):
        if self.period <= 0:
            raise ValueError(f"period must be positive, got {self.period}")
        if not (0.0 < self.duty_factor <= 1.0):
            raise ValueError(
                f"duty_factor must be in (0, 1], got {self.duty_factor}"
            )
        if len(self.legs) != 4:
            raise ValueError(
                f"GaitSpec needs exactly 4 leg specs, got {len(self.legs)}"
            )
