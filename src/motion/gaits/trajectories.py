"""
Foot-trajectory shape library.

Single home for the per-axis trajectory *shapes* used to build gaits: the
stride curves, the lift/clearance profiles, and the lateral sway patterns. These
are pure functions of a step count (and shape-only parameters) returning a 1-D
numpy array over the cycle. Amplitude/distance/clearance scaling is applied by
the caller, so each function returns the unscaled shape.

This consolidates the trajectory math that currently lives in two places:
`Gait`'s instance methods (`stride_forward`, `downupdown`, …) and
`MovementPattern`'s staticmethods in simplified_gait.py. The bodies here are
byte-for-byte equivalent to both (see test/test_gait_spec.py parity tests); the
duplicated originals delegate to or are retired in favor of this module as gaits
migrate onto GaitSpec (plan units U5-U8).

See docs/plans/2026-05-30-001-refactor-gait-core-phasing-plan.md.
"""

from __future__ import annotations

import numpy as np


def stride_forward(steps: int) -> np.ndarray:
    """Forward half-stride: sin ramp 0 -> 1 over [0, 90] degrees."""
    return np.sin(np.radians(np.linspace(0, 90, steps)))


def stride_home(steps: int) -> np.ndarray:
    """Return-to-center: cos ramp 1 -> 0 over [0, 90] degrees."""
    return np.cos(np.radians(np.linspace(0, 90, steps)))


def stride_back(steps: int) -> np.ndarray:
    """Backward half-stride: cos ramp 0 -> -1 over [90, 180] degrees."""
    return np.cos(np.radians(np.linspace(90, 180, steps)))


def stride_front_to_back(steps: int) -> np.ndarray:
    """Full stride front-to-back: cos 1 -> -1 over [0, 180] degrees."""
    return np.cos(np.radians(np.linspace(0, 180, steps)))


def downupdown(steps: int) -> np.ndarray:
    """Lift profile with a brief downward press before the lift: the first fifth
    dips slightly (sin over [-10, 0] deg), then the rest lifts (sin over
    [45, 180] deg). Caller scales by -clearance."""
    ns1 = int(steps / 5)
    ns2 = steps - ns1
    return np.hstack([
        np.sin(np.radians(np.linspace(-10, 0, ns1))),
        np.sin(np.radians(np.linspace(45, 180, ns2))),
    ])


def updown(steps: int, fast: bool = True) -> np.ndarray:
    """Simple lift: fast starts mid-swing (sin over [45, 180] deg); non-fast is a
    full sin arch over [0, 180] deg."""
    if fast:
        return np.sin(np.radians(np.linspace(45, 180, steps)))
    return np.sin(np.radians(np.linspace(0, 180, steps)))


def lift(steps: int) -> np.ndarray:
    """Symmetric up-and-down arch over [0, pi]. Caller scales by height."""
    return np.sin(np.linspace(0, np.pi, steps))


def lateral_sway(steps: int) -> np.ndarray:
    """Full sinusoidal sway over [0, 2pi]. Caller scales by amplitude."""
    return np.sin(np.linspace(0, 2 * np.pi, steps))


def trot_lateral_pattern(num_steps: int) -> np.ndarray:
    """Trot-specific hip-sway shape across a full cycle (num_steps * 4 long).
    Caller scales by hip_sway amplitude."""
    return np.hstack([
        np.sin(np.linspace(0, np.pi, num_steps)) * 0.7,
        np.sin(np.linspace(np.pi, 2 * np.pi, num_steps)) * 0.3,
        np.sin(np.linspace(0, np.pi, num_steps * 2)) * 0.2,
    ])


def step_cycle(steps: int) -> np.ndarray:
    """Complete forward-home-back stride cycle (unscaled). Length is
    4 * (steps // 4), matching the original MovementPattern.step_cycle."""
    steps_per_part = steps // 4
    return np.concatenate([
        stride_forward(steps_per_part),
        stride_home(steps_per_part),
        stride_back(steps_per_part * 2),
    ])


def zero(steps: int) -> np.ndarray:
    """No movement."""
    return np.zeros(steps)
