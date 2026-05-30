"""
Trot migration equality (plan U5).

`Trot` and `SimpleTrotWithLateral` now build through GaitSpec/compile_spec instead
of hand-rolled step arrays. These tests prove the migration is byte-identical by
comparing against an INDEPENDENT reconstruction of the pre-migration build_steps
algorithm (the `_legacy_*` helpers below) -- a characterization oracle that does
not call the production build_steps, so it can't drift with it.

The systemic behavior (reachability, periodicity, skid ceilings) is additionally
locked by test/test_gaits.py, which still passes unchanged. The structural tests
here pin the two things most likely to break in a spec rewrite: the diagonal weld
and the negated, half-cycle-rolled lateral column (the load-bearing y-sign flip).
"""

import numpy as np

from settings import settings
from src.motion.gaits.trot import Trot
from src.motion.gaits.simplified_gait import SimpleTrotWithLateral


# --- independent reconstruction of the legacy build_steps -------------------

def _reshape(x, y, z, n):
    return np.array([x, y, z]).reshape(-1, n).transpose(1, 0).astype(int)


def _downupdown(num):
    ns1 = int(num / 5)
    ns2 = num - ns1
    return np.hstack([
        np.sin(np.radians(np.linspace(-10, 0, ns1))),
        np.sin(np.radians(np.linspace(45, 180, ns2))),
    ])


def _trot_lateral(num):
    return np.hstack([
        np.sin(np.linspace(0, np.pi, num)) * 0.7,
        np.sin(np.linspace(np.pi, 2 * np.pi, num)) * 0.3,
        np.sin(np.linspace(0, np.pi, num * 2)) * 0.2,
    ])


def _legacy_x(num, stride):
    return np.hstack([
        np.sin(np.radians(np.linspace(0, 90, num))),
        np.cos(np.radians(np.linspace(0, 90, num))),
        np.cos(np.radians(np.linspace(90, 180, num * 2))),
    ]) * int(stride)


def _legacy_z(num, clearance):
    return np.hstack([_downupdown(num), np.zeros(num * 3)]) * (-clearance)


def _legacy_trot(num, stride, clearance):
    x = _legacy_x(num, stride)
    y = np.zeros(num * 4)
    z = _legacy_z(num, clearance)
    s1 = _reshape(x, y, z, num * 4)
    s2 = np.roll(s1, num * 2, axis=0)
    return np.stack([s1, s2, s1, s2])


def _legacy_simple_trot(num, stride, clearance, hip):
    x = _legacy_x(num, stride)
    y = _trot_lateral(num) * hip
    z = _legacy_z(num, clearance)
    s1 = _reshape(x, y, z, num * 4)
    s2x = np.roll(x, num * 2)
    s2y = -np.roll(y, num * 2)
    s2z = np.roll(z, num * 2)
    s2 = _reshape(s2x, s2y, s2z, num * 4)
    return np.stack([s1, s2, s1, s2])


# --- byte-equality vs the legacy oracle -------------------------------------

def test_trot_in_place_matches_legacy():
    g = Trot(params=settings.trot_in_place_params)
    expected = _legacy_trot(g.num_steps, g.stride, g.clearance)
    assert np.array_equal(g.steps, expected)


def test_simple_trot_forward_matches_legacy():
    g = SimpleTrotWithLateral(
        p0=settings.position_trot + settings.position_forward_offsets,
        params=settings.trot_params,
    )
    expected = _legacy_simple_trot(g.num_steps, g.stride, g.clearance, g.hip_sway)
    assert np.array_equal(g.steps, expected)


def test_simple_trot_backward_matches_legacy():
    g = SimpleTrotWithLateral(
        p0=settings.position_trot + settings.position_backward_offsets,
        params=settings.trot_reverse_params,
    )
    expected = _legacy_simple_trot(g.num_steps, g.stride, g.clearance, g.hip_sway)
    assert np.array_equal(g.steps, expected)


# --- structural guarantees the rewrite must keep ----------------------------

def test_trot_welds_diagonal_pairs():
    g = SimpleTrotWithLateral(
        p0=settings.position_trot + settings.position_forward_offsets,
        params=settings.trot_params,
    )
    assert np.array_equal(g.steps[0], g.steps[2])
    assert np.array_equal(g.steps[1], g.steps[3])


def test_lateral_trot_preserves_y_sign_flip():
    g = SimpleTrotWithLateral(
        p0=settings.position_trot + settings.position_forward_offsets,
        params=settings.trot_params,
    )
    n = g.max_index
    # leg 1's lateral column is leg 0's, negated and rolled a half cycle.
    assert np.array_equal(g.steps[1][:, 1], -np.roll(g.steps[0][:, 1], n // 2))
    # and the lateral motion is genuinely present (the flip is load-bearing).
    assert np.any(g.steps[0][:, 1] != 0)
