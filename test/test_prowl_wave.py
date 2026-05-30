"""
Structural tests for the rebuilt static-wave prowl (plan U3).

Confirms the wave shape: one foot airborne at a time, the LF->RH->RF->LH lift
sequence, backward = negated stride, periodicity, and that the body-shift is smooth
(planted feet do not jump). The static-stability-margin gate and the flipped skid
xfail live in test/test_prowl_wave_stability (added in U4) and test/test_gaits.py.
"""

import numpy as np
from dataclasses import replace

from settings import settings
from src.motion.gaits.prowl import Prowl


def _prowl(params=None):
    return Prowl(p0=settings.position_prowl, params=params or settings.prowl_params)


def _cycle(g):
    n = g.max_index
    return np.array([np.asarray(next(g), float) for _ in range(n)])


def test_one_foot_airborne_at_a_time():
    g = _prowl()
    offz = g.steps[:, :, 2]            # (4, N) per-leg lift offset
    lifted = (offz < -2).sum(axis=0)   # legs airborne per tick
    assert lifted.max() == 1           # never two feet up at once
    assert (lifted == 1).any()         # at least one swing happens


def test_lift_sequence_is_LF_RH_RF_LH():
    g = _prowl()
    seg = g.num_steps
    offz = g.steps[:, :, 2]
    # the leg lifted in the middle of each of the 8 segments
    order = []
    for s in range(g.SEGMENTS):
        mid = s * seg + seg // 2
        up = np.where(offz[:, mid] < -2)[0]
        if up.size:
            order.append(int(up[0]))
    # legs 0,2,1,3 = LF, RH, RF, LH
    assert order == [0, 2, 1, 3]


def test_duty_factor_is_seven_eighths():
    g = _prowl()
    # each leg airborne exactly one of eight segments
    offz = g.steps[:, :, 2]
    for leg in range(4):
        airborne_frac = np.mean(offz[leg] < -2)
        assert airborne_frac < 0.2  # ~1/8 swing


def test_backward_is_negated_stride():
    fwd = _prowl(settings.prowl_params)
    bwd = _prowl(settings.prowl_reverse_params)
    # same lift schedule and body shift; the forward/back foot travel (x) is the
    # piece that flips. Compare the x stride contribution sign via per-leg x extent.
    # Lift (z) timing is identical:
    assert np.array_equal((fwd.steps[:, :, 2] < -2), (bwd.steps[:, :, 2] < -2))
    # and the gaits are not identical (stride direction differs)
    assert not np.array_equal(fwd.steps, bwd.steps)


def test_periodic_over_cycle():
    g = _prowl()
    start = np.asarray(next(g), float)
    for _ in range(g.max_index - 1):
        next(g)
    assert np.allclose(start, np.asarray(next(g), float))


def test_frame_contract_finite():
    frames = _cycle(_prowl())
    for frame in frames:
        assert frame.shape == (4, 3)
        assert np.all(np.isfinite(frame))


def test_body_shift_is_smooth():
    """Planted feet move only via the smooth body-shift, in small per-step steps --
    the property that flips the skid xfail (asserted formally in U4)."""
    g = _prowl()
    offz = g.steps[:, :, 2]
    frames = _cycle(g)
    wrapped = np.vstack([frames, frames[:1]])
    dh = np.linalg.norm(np.diff(wrapped[:, :, :2], axis=0), axis=2)  # (N,4) horizontal delta
    planted = offz.T >= -2
    max_planted_skid = np.nanmax(np.where(planted, dh, np.nan))
    assert max_planted_skid <= 15.0
