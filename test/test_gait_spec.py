"""
Tests for the GaitSpec compiler and the consolidated trajectory library (plan U3).

Two concerns:
- `compile_spec` turns a declarative GaitSpec into the canonical (4, N, 3) step
  array, realizing each leg's phase offset as the exact integer roll the legacy
  gaits perform (so later migration is byte-identical).
- `trajectories.py` is byte-for-byte equivalent to the existing `Gait` instance
  methods and `MovementPattern` staticmethods it consolidates -- the parity tests
  are the safety net that lets U5-U8 swap gaits onto it without behavior drift.

Additive unit: no production gait is wired to the compiler yet.
"""

import numpy as np
import pytest

from settings import settings
from src.motion.gaits import trajectories as T
from src.motion.gaits.gait_spec import GaitSpec, LegSpec, compile_spec
from src.motion.gaits.simplified_gait import MovementPattern as MP
from src.motion.gaits.trot import Trot


# --- compile_spec -----------------------------------------------------------

def test_compile_two_group_matches_hand_roll():
    """phi=[0,.5,0,.5] reproduces a hand-rolled [base, roll(base, N/2)] -- the
    diagonal trot structure."""
    n = 24
    patt = lambda steps: np.linspace(0, 50, steps)
    spec = GaitSpec(
        period=n, duty_factor=0.75,
        legs=[LegSpec(phase_offset=p, x=patt) for p in (0.0, 0.5, 0.0, 0.5)],
    )
    steps = compile_spec(spec)
    base = steps[0]
    assert steps.shape == (4, n, 3)
    assert np.array_equal(steps[2], base)                          # phi=0
    assert np.array_equal(steps[1], np.roll(base, n // 2, axis=0))  # phi=0.5
    assert np.array_equal(steps[3], steps[1])


def test_compile_four_leg_matches_tiger_rolls():
    """phi=[0,.25,.5,.75] reproduces graveyard tiger_run's num_steps*{1,2,3}
    rolls -- the wave structure."""
    num = 6
    n = num * 4  # 24
    patt = lambda steps: np.linspace(0, 100, steps)
    spec = GaitSpec(
        period=n, duty_factor=0.75,
        legs=[LegSpec(phase_offset=p, x=patt) for p in (0.0, 0.25, 0.5, 0.75)],
    )
    steps = compile_spec(spec)
    base = steps[0]
    assert np.array_equal(steps[1], np.roll(base, num, axis=0))
    assert np.array_equal(steps[2], np.roll(base, num * 2, axis=0))
    assert np.array_equal(steps[3], np.roll(base, num * 3, axis=0))


def test_compile_per_leg_y_sign_flip():
    """A leg declaring -y of its pair produces the exact negation of that y column
    (the load-bearing lateral flip, expressed in the spec not in kinematics)."""
    n = 24
    yf = lambda steps: np.linspace(0, 30, steps)
    spec = GaitSpec(
        period=n, duty_factor=0.75,
        legs=[LegSpec(y=yf), LegSpec(y=lambda s: -yf(s)), LegSpec(), LegSpec()],
    )
    steps = compile_spec(spec)
    assert np.array_equal(steps[1][:, 1], -steps[0][:, 1])


def test_compile_shape_and_int_dtype():
    n = 20
    spec = GaitSpec(
        period=n, duty_factor=0.75,
        legs=[LegSpec(x=lambda s: np.linspace(0, 9, s)) for _ in range(4)],
    )
    steps = compile_spec(spec)
    assert steps.shape == (4, n, 3)
    assert np.issubdtype(steps.dtype, np.integer)


def test_compile_none_axis_is_zeros():
    n = 12
    spec = GaitSpec(
        period=n, duty_factor=0.75,
        legs=[LegSpec(x=lambda s: np.ones(s) * 5) for _ in range(4)],
    )
    steps = compile_spec(spec)
    assert np.array_equal(steps[0][:, 1], np.zeros(n))  # y not declared
    assert np.array_equal(steps[0][:, 2], np.zeros(n))  # z not declared


def test_compile_zero_phase_is_no_roll():
    n = 16
    patt = lambda steps: np.arange(steps, dtype=float)
    spec = GaitSpec(
        period=n, duty_factor=0.75,
        legs=[LegSpec(phase_offset=0.0, x=patt) for _ in range(4)],
    )
    steps = compile_spec(spec)
    assert np.array_equal(steps[0][:, 0], np.arange(n))


# --- trajectory parity: trajectories.py == existing sources -----------------

_g = Trot(params=settings.trot_in_place_params)  # instance for Gait methods
_N = _g.num_steps


def test_trajectories_match_gait_methods():
    assert np.array_equal(T.stride_forward(_N), _g.stride_forward())
    assert np.array_equal(T.stride_home(_N), _g.stride_home())
    assert np.array_equal(T.stride_back(_N), _g.stride_back())
    assert np.array_equal(T.stride_front_to_back(_N), _g.stride_front_to_back())
    assert np.array_equal(T.downupdown(_N), _g.downupdown())
    assert np.array_equal(T.updown(_N, fast=True), _g.updown())
    assert np.array_equal(
        T.updown(_N, fast=False), _g.updown(mode=type(_g).UpdownMode.normal)
    )


def test_trajectories_match_movement_pattern():
    assert np.array_equal(T.stride_forward(_N), MP.stride_forward(_N))
    assert np.array_equal(T.stride_home(_N), MP.stride_home(_N))
    assert np.array_equal(T.stride_back(_N), MP.stride_back(_N))
    assert np.array_equal(T.downupdown(_N), MP.downupdown(_N))        # clearance=1.0
    assert np.array_equal(T.lift(_N), MP.lift(_N))                    # height=1.0
    assert np.array_equal(T.lateral_sway(_N), MP.lateral_sway(_N))
    assert np.array_equal(T.trot_lateral_pattern(_N), MP.trot_lateral_pattern(_N))
    assert np.array_equal(T.step_cycle(_N), MP.step_cycle(_N))
    assert np.array_equal(T.zero(_N), MP.zero(_N))


def test_trajectories_scale_composes_like_originals():
    """The library returns unscaled shapes; applying the caller's scale reproduces
    the scaled MovementPattern outputs."""
    assert np.array_equal(T.lift(_N) * 7.0, MP.lift(_N, 7.0))
    assert np.array_equal(T.downupdown(_N) * 3.0, MP.downupdown(_N, 3.0))
    assert np.array_equal(T.trot_lateral_pattern(_N) * 4.0, MP.trot_lateral_pattern(_N, 4.0))
