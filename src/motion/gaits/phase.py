"""
Phase model for gait scheduling.

Standard quadruped gait formulation (McGhee & Frank lineage; see
docs/plans/2026-05-30-001-refactor-gait-core-phasing-plan.md and the MIT Cheetah /
Stanford Pupper gait schedulers).

A gait is described by three things:
    period N         -- number of discrete ticks in one full cycle
    duty_factor beta -- fraction of the cycle each foot is in STANCE, in (0, 1]
    phase_offset phi -- per-leg cycle offset, in [0, 1)

At a normalized cycle position theta in [0, 1):
    local_phase(theta, phi) = (theta + phi) mod 1
    in_stance               = local_phase < beta
    swing_phase             = (local_phase - beta) / (1 - beta)   when in swing

This module is intentionally pure math: scalar in, scalar out, no NumPy state and
no I/O. It underpins the declarative GaitSpec but does not itself construct any
gait. The integer-tick bridge (`phase_to_ticks`) is what lets the existing
index-based gait iterator realize a continuous phase offset as the same
`np.roll(..., k)` the current gaits already perform -- the behavior-preserving
link between the declarative model and the precomputed step arrays.
"""

from __future__ import annotations


def _normalize(phase: float) -> float:
    """Wrap a phase into [0, 1). Phase is periodic, so negative and >1 values are
    valid inputs and fold back in (e.g. -0.25 -> 0.75, 1.25 -> 0.25)."""
    return phase % 1.0


def phase_to_ticks(phase: float, period: int) -> int:
    """Realize a continuous phase offset as an integer tick roll over `period`
    ticks.

    This is the bridge to the index-based iterator: a leg with phase_offset phi
    is the base trajectory rolled by `phase_to_ticks(phi, N)` ticks. At N=24 the
    quarter offsets map to 0/6/12/18 -- exactly the rolls the current gaits and
    `graveyard/gaits/tiger_run.py` perform by hand.

    The result is always in [0, period): a phase just below 1.0 that would round
    up to `period` wraps back to 0, so the roll amount never equals a full cycle.
    """
    if period <= 0:
        raise ValueError(f"period must be positive, got {period}")
    return int(round(_normalize(phase) * period)) % period


def local_phase(theta: float, phase_offset: float) -> float:
    """The leg's own cycle position given global position `theta` and its offset."""
    return _normalize(theta + phase_offset)


def in_stance(theta: float, phase_offset: float, duty_factor: float) -> bool:
    """True when the leg is in stance (foot loaded) at global position `theta`.

    Stance occupies the first `duty_factor` fraction of each leg's local cycle;
    the strict `<` makes the stance/swing boundary unambiguous, so uniformly
    spaced wave offsets tile with exactly one leg swinging at a time."""
    return local_phase(theta, phase_offset) < duty_factor


def swing_phase(theta: float, phase_offset: float, duty_factor: float):
    """Progress through the swing window, in [0, 1), or None while in stance.

    Returns None during stance (swing progress is undefined there) and when
    `duty_factor >= 1.0` (a gait with no swing window). At the instant swing
    begins (local_phase == duty_factor) this is 0.0 and it approaches 1.0 as the
    swing completes. The returned scalar is what a foot-trajectory layer consumes
    to shape the swing curve, with no knowledge of timing."""
    lp = local_phase(theta, phase_offset)
    if lp < duty_factor:
        return None
    if duty_factor >= 1.0:
        return None
    return (lp - duty_factor) / (1.0 - duty_factor)
