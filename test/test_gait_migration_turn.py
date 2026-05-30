"""
Turn migration equality (plan U7).

`Turn` now builds through GaitSpec/compile_spec using four explicit per-leg
LegSpecs (turn is the genuine 4-independent-leg gait -- each leg lifts in its own
segment of a 5-segment cycle, all returning laterally together in the last). These
tests prove byte-identity against an INDEPENDENT reconstruction of the legacy
build_steps, across all four production variants, plus the structural guarantees:
four independent legs (no weld) and the turn_direction lateral-sign flip.
"""

import numpy as np
import pytest
from dataclasses import replace

from settings import settings
from src.motion.gaits.turn import Turn

_VARIANTS = {
    "fwd_lt": dict(turn_direction=1),
    "fwd_rt": dict(turn_direction=-1),
    "bwd_lt": dict(turn_direction=-1, is_reversed=True),
    "bwd_rt": dict(turn_direction=1, is_reversed=True),
}


def _legacy_turn(num, stride, clearance, direction):
    """Independent reconstruction of the pre-migration Turn.build_steps."""
    mag_y, mag_z = -stride, -clearance
    n = num * 5
    step = np.sin(np.radians(np.linspace(0, 90, num))) * mag_y * direction
    back = np.cos(np.radians(np.linspace(0, 90, num))) * mag_y * direction
    up = np.sin(np.radians(np.linspace(0, 180, num))) * mag_z
    o = np.zeros(num)
    z = np.zeros(n)

    def reshape(rows):
        return np.array(rows).reshape(-1, n).transpose(1, 0).astype(int)

    s1 = reshape([z, np.hstack([step, o, o, o, back]), np.hstack([up, o, o, o, o])])
    s2 = reshape([z, np.hstack([o, step, o, o, back]), np.hstack([o, up, o, o, o])])
    s3 = reshape([z, np.hstack([o, o, -step, o, back]), np.hstack([o, o, up, o, o])])
    s4 = reshape([z, np.hstack([o, o, o, -step, back]), np.hstack([o, o, o, up, o])])
    return np.stack([s1, s2, s3, s4])


@pytest.mark.parametrize("name", list(_VARIANTS))
def test_turn_matches_legacy(name):
    g = Turn(params=replace(settings.turn_params, **_VARIANTS[name]))
    expected = _legacy_turn(g.num_steps, g.stride, g.clearance, g.turn_direction)
    assert np.array_equal(g.steps, expected)


def test_turn_uses_four_independent_legs():
    g = Turn(params=replace(settings.turn_params, turn_direction=1))
    # not welded: legs 2,3 differ from legs 0,1
    assert not np.array_equal(g.steps[0], g.steps[2])
    assert not np.array_equal(g.steps[1], g.steps[3])
    # each leg lifts in a distinct segment of the 5-segment cycle
    lift_tick = [int(np.argmin(g.steps[i][:, 2])) for i in range(4)]
    assert len(set(lift_tick)) == 4


def test_turn_direction_flips_lateral_only():
    lt = Turn(params=replace(settings.turn_params, turn_direction=1))
    rt = Turn(params=replace(settings.turn_params, turn_direction=-1))
    assert np.array_equal(lt.steps[:, :, 1], -rt.steps[:, :, 1])  # y negated
    assert np.array_equal(lt.steps[:, :, 2], rt.steps[:, :, 2])   # lift identical
