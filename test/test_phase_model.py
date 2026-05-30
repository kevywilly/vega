"""
Tests for the gait phase model (plan U1).

Covers the pure phase math in src/motion/gaits/phase.py and the GaitSpec/LegSpec
schema validation in src/motion/gaits/gait_spec.py. These have no production
wiring yet -- this unit is additive.

The load-bearing property is that phase offsets realize as the same integer tick
rolls the current gaits already perform (so later migration is byte-identical),
and that a beta=0.75 wave gait tiles with exactly one leg swinging at a time
(proving the model can express what the welded 2-group core cannot).
"""

import numpy as np
import pytest

from src.motion.gaits.phase import (
    phase_to_ticks,
    local_phase,
    in_stance,
    swing_phase,
)
from src.motion.gaits.gait_spec import GaitSpec, LegSpec


# --- phase_to_ticks: the index-based bridge ---------------------------------

@pytest.mark.parametrize("phi,expected", [(0.0, 0), (0.25, 6), (0.5, 12), (0.75, 18)])
def test_phase_to_ticks_matches_quarter_rolls(phi, expected):
    """Quarter-cycle offsets at N=24 map to the exact rolls used by the current
    gaits (num_steps*2 half-cycle) and graveyard tiger_run (num_steps*{1,2,3})."""
    assert phase_to_ticks(phi, 24) == expected


def test_phase_to_ticks_wraps_at_one():
    assert phase_to_ticks(1.0, 24) == phase_to_ticks(0.0, 24) == 0


@pytest.mark.parametrize("phi,expected", [(-0.25, 18), (1.25, 6), (2.0, 0)])
def test_phase_to_ticks_normalizes_out_of_range(phi, expected):
    """Phase is periodic; negative and >1 offsets fold back into [0, 1)."""
    assert phase_to_ticks(phi, 24) == expected


def test_phase_to_ticks_never_equals_period():
    """A phase just under 1.0 must wrap to 0, never to a full-cycle roll."""
    assert phase_to_ticks(0.999, 24) == 0
    for n in (6, 12, 24, 28, 30):
        assert 0 <= phase_to_ticks(0.999999, n) < n


def test_phase_to_ticks_rejects_nonpositive_period():
    with pytest.raises(ValueError):
        phase_to_ticks(0.5, 0)


# --- local_phase / in_stance / swing_phase ----------------------------------

def test_local_phase_wraps():
    assert local_phase(0.6, 0.5) == pytest.approx(0.1)
    assert local_phase(0.0, 0.0) == 0.0
    assert local_phase(0.8, 0.5) == pytest.approx(0.3)


def test_in_stance_fraction_matches_duty_factor():
    """A leg is in stance for exactly `duty_factor` of the cycle."""
    thetas = np.linspace(0, 1, 1000, endpoint=False)
    for beta in (0.5, 0.75, 0.8):
        frac = np.mean([in_stance(t, 0.0, beta) for t in thetas])
        assert frac == pytest.approx(beta, abs=0.01)


def test_swing_phase_stance_returns_none():
    # theta=0 with phi=0 is the very start of stance
    assert swing_phase(0.0, 0.0, 0.75) is None


def test_swing_phase_ranges_zero_to_one():
    beta = 0.75
    # at the instant swing starts, progress is 0
    assert swing_phase(0.75, 0.0, beta) == pytest.approx(0.0)
    # late in the swing window, progress approaches 1
    assert swing_phase(0.99, 0.0, beta) == pytest.approx((0.99 - 0.75) / 0.25)
    # every swing value stays in [0, 1)
    for t in np.linspace(0, 1, 1000, endpoint=False):
        sp = swing_phase(t, 0.0, beta)
        if sp is not None:
            assert 0.0 <= sp < 1.0


def test_swing_phase_none_when_no_swing_window():
    # duty_factor == 1.0 means the foot is always in stance: no swing ever
    for t in np.linspace(0, 1, 100, endpoint=False):
        assert swing_phase(t, 0.0, 1.0) is None


def test_wave_gait_tiles_one_leg_swinging():
    """beta=0.75 with offsets [0, .25, .5, .75] keeps exactly one leg in swing at
    every instant -- the static wave gait the welded 2-group core cannot express."""
    beta = 0.75
    offsets = [0.0, 0.25, 0.5, 0.75]
    for t in np.linspace(0, 1, 1000, endpoint=False):
        swinging = sum(not in_stance(t, phi, beta) for phi in offsets)
        assert swinging == 1, f"theta={t}: {swinging} legs swinging, expected 1"


# --- GaitSpec / LegSpec schema validation -----------------------------------

def test_gaitspec_accepts_valid_four_leg_wave():
    spec = GaitSpec(
        period=24,
        duty_factor=0.75,
        legs=[LegSpec(phase_offset=p) for p in (0.0, 0.25, 0.5, 0.75)],
    )
    assert spec.period == 24
    assert len(spec.legs) == 4
    assert spec.legs[2].phase_offset == 0.5


def test_gaitspec_requires_exactly_four_legs():
    with pytest.raises(ValueError):
        GaitSpec(period=24, duty_factor=0.75, legs=[LegSpec(), LegSpec()])


@pytest.mark.parametrize("beta", [0.0, -0.1, 1.5])
def test_gaitspec_rejects_out_of_range_duty_factor(beta):
    with pytest.raises(ValueError):
        GaitSpec(period=24, duty_factor=beta, legs=[LegSpec() for _ in range(4)])


def test_gaitspec_rejects_nonpositive_period():
    with pytest.raises(ValueError):
        GaitSpec(period=0, duty_factor=0.75, legs=[LegSpec() for _ in range(4)])


def test_legspec_defaults_are_no_motion():
    leg = LegSpec()
    assert leg.phase_offset == 0.0
    assert leg.x is None and leg.y is None and leg.z is None
