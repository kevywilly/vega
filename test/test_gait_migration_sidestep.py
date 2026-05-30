"""
Sidestep migration equality (plan U6).

`SimpleSidestep` now builds through GaitSpec/compile_spec and inherits Gait
directly (it previously went through SimplifiedGait, whose build_steps only read
legs 0,1 and welded the rest). These tests prove byte-identity against an
INDEPENDENT reconstruction of the realized legacy behavior.

Important: the legacy define_leg_movements dict nominally gave legs 2,3 their own
phases, but that never ran -- the realized gait welds legs 2,3 onto 0,1. The
oracle here reproduces the *realized* behavior (the weld), which is what
byte-identity must preserve.
"""

import numpy as np
from dataclasses import replace

from settings import settings
from src.motion.gaits.simplified_gait import SimpleSidestep


def _sf(n):
    return np.sin(np.radians(np.linspace(0, 90, n)))


def _sh(n):
    return np.cos(np.radians(np.linspace(0, 90, n)))


def _sb(n):
    return np.cos(np.radians(np.linspace(90, 180, n)))


def _lift(n):
    return np.sin(np.linspace(0, np.pi, n))


def _reshape(x, y, z, n):
    return np.array([x, y, z]).reshape(-1, n).transpose(1, 0).astype(int)


def _legacy_sidestep(num, stride, clearance):
    """Independent reconstruction of the realized pre-migration SimpleSidestep:
    y = step_cycle, z = lift over the first num ticks, legs welded with the second
    diagonal pair rolled by num ticks (phase_shift = num_steps)."""
    n = num * 4
    y = np.concatenate([_sf(num), _sh(num), _sb(num * 2)]) * stride
    z = np.zeros(n)
    z[:num] = _lift(num) * (-clearance)
    x = np.zeros(n)
    s1 = _reshape(x, y, z, n)
    rs = num  # legacy phase_shift = num_steps
    s2 = _reshape(np.roll(x, rs), np.roll(y, rs), np.roll(z, rs), n)
    return np.stack([s1, s2, s1, s2])


def test_sidestep_right_matches_legacy():
    g = SimpleSidestep(params=settings.sidestep_params)
    expected = _legacy_sidestep(g.num_steps, g.stride, g.clearance)
    assert np.array_equal(g.steps, expected)


def test_sidestep_left_matches_legacy():
    g = SimpleSidestep(params=replace(settings.sidestep_params, is_reversed=True))
    expected = _legacy_sidestep(g.num_steps, g.stride, g.clearance)
    assert np.array_equal(g.steps, expected)


def test_sidestep_welds_diagonal_pairs():
    g = SimpleSidestep(params=settings.sidestep_params)
    assert np.array_equal(g.steps[0], g.steps[2])
    assert np.array_equal(g.steps[1], g.steps[3])


def test_left_is_negated_right_stride():
    r = SimpleSidestep(params=settings.sidestep_params)
    l = SimpleSidestep(params=replace(settings.sidestep_params, is_reversed=True))
    # LEFT vs RIGHT is purely the sign of the lateral (y) column; lift (z) is identical.
    assert np.array_equal(l.steps[:, :, 1], -r.steps[:, :, 1])
    assert np.array_equal(l.steps[:, :, 2], r.steps[:, :, 2])
