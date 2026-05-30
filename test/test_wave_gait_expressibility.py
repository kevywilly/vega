"""
Wave-gait expressibility proof (plan U4).

The whole point of the gait-core refactor (U1-U3) is to make a one-leg-at-a-time
static wave gait *expressible* -- something the legacy welded 2-group core could
not represent. This test constructs such a gait declaratively via GaitSpec +
compile_spec, drops it into the generalized Gait core, and proves it:

  - produces valid, reachable, periodic motion,
  - keeps at most one foot off the ground at a time (the wave property), and
  - is genuinely 4-phase -- which the welded path provably collapses.

It is a proof fixture only: no production gait class is added and nothing is
registered in controller._get_gait_factory. The actual production wave gait
(prowl rebuild) is plan item 4, downstream of this.
"""

import numpy as np
import pytest

from settings import settings
from src.motion.kinematics import QuadrupedKinematics
from src.motion.gaits.gait import Gait
from src.motion.gaits.gait_spec import GaitSpec, LegSpec, compile_spec
from src.motion.gaits.phase import in_stance
from src.motion.gaits import trajectories as T

_km = QuadrupedKinematics(
    settings.coxa_length, settings.femur_length, settings.tibia_length,
    settings.robot_width, settings.robot_length,
)

BETA = 0.75                       # stance fraction: wave needs beta >= (n-1)/n = 0.75
PHASES = (0.0, 0.25, 0.5, 0.75)   # one leg swings per quarter-cycle, tiling with no overlap
CLEARANCE = 40.0
STRIDE = 30.0


def _base_x(n):
    swing, stance = n // 4, n - n // 4
    return np.concatenate([np.linspace(0, STRIDE, swing), np.linspace(STRIDE, 0, stance)])


def _base_z(n):
    # foot lifts (negative offset) only during its swing window, flat on the ground otherwise
    swing, stance = n // 4, n - n // 4
    return np.concatenate([T.lift(swing) * -CLEARANCE, np.zeros(stance)])


def _wave_spec(num_steps):
    n = num_steps * 4
    return GaitSpec(
        period=n,
        duty_factor=BETA,
        legs=[LegSpec(phase_offset=phi, x=_base_x, z=_base_z) for phi in PHASES],
    )


class _WaveGait(Gait):
    """A static wave gait built declaratively -- the gait the welded core couldn't
    express. build_steps sets self.steps directly from the compiled spec."""

    def build_steps(self):
        self.steps = compile_spec(_wave_spec(self.num_steps))


def _wave():
    return _WaveGait(p0=settings.position_ready)


def _cycle(gait):
    n = gait.max_index
    return np.array([np.asarray(next(gait), float) for _ in range(n + 1)])


# --- the wave gait is valid motion ------------------------------------------

def test_frame_contract_finite():
    frames = _cycle(_wave())
    for frame in frames:
        assert frame.shape == (4, 3)
        assert np.all(np.isfinite(frame))


def test_all_feet_reachable_through_cycle():
    g = _wave()
    frames = _cycle(g)
    for t, frame in enumerate(frames):
        for leg in range(4):
            assert _km.validate_position(frame[leg]), f"leg {leg} unreachable at t={t}"


def test_periodic_over_max_index():
    g = _wave()
    start = np.asarray(next(g), float)
    for _ in range(g.max_index - 1):
        next(g)
    assert np.allclose(start, np.asarray(next(g), float))


# --- the wave property -------------------------------------------------------

def test_at_most_one_foot_lifted_per_tick():
    """The realized motion never has two feet off the ground at once."""
    steps = _wave().steps  # (4, N, 3)
    offz = steps[:, :, 2]  # per-leg z offset over the cycle
    for t in range(offz.shape[1]):
        lifted = int(np.sum(offz[:, t] < -1.0))
        assert lifted <= 1, f"t={t}: {lifted} feet lifted"


def test_exactly_one_leg_in_swing_by_schedule():
    """By the phase schedule (beta=0.75, quarter-spaced offsets) exactly one leg is
    in its swing window at every tick -- the McGhee wave-tiling condition."""
    n = _wave().max_index
    for t in range(n):
        theta = t / n
        swinging = sum(not in_stance(theta, phi, BETA) for phi in PHASES)
        assert swinging == 1, f"t={t}: {swinging} legs scheduled to swing"


def test_wave_is_genuinely_four_phase():
    g = _wave()
    # each leg's deepest lift falls in a distinct tick window -> 4 independent phases
    lift_tick = [int(np.argmin(g.steps[i][:, 2])) for i in range(4)]
    assert len(set(lift_tick)) == 4


# --- the ceiling: the welded 2-group path cannot express this ---------------

class _WeldedTwoGroup(Gait):
    """The legacy authoring path: only steps1 (legs 0,2) and steps2 (legs 1,3) are
    set, so assembly welds legs 2,3 onto 0,1. It cannot place four distinct phases."""

    leg0 = None
    leg1 = None

    def build_steps(self):
        self.steps1 = type(self).leg0
        self.steps2 = type(self).leg1


def test_wave_not_expressible_through_welded_path():
    wave = _wave()
    lift_tick = [int(np.argmin(wave.steps[i][:, 2])) for i in range(4)]

    # Feed the wave's leg0/leg1 base arrays through the real legacy 2-group path.
    _WeldedTwoGroup.leg0 = wave.steps[0]
    _WeldedTwoGroup.leg1 = wave.steps[1]
    welded = _WeldedTwoGroup(p0=settings.position_ready)

    # Assembly forces legs 2,3 to mirror 0,1 -- the ceiling.
    assert np.array_equal(welded.steps[2], welded.steps[0])
    assert np.array_equal(welded.steps[3], welded.steps[1])

    # So the welded "leg 2" lifts in lockstep with leg 0, NOT at the wave's leg-2
    # window: the one-leg-at-a-time schedule is unrepresentable here.
    welded_leg2_lift = int(np.argmin(welded.steps[2][:, 2]))
    assert welded_leg2_lift == lift_tick[0]
    assert welded_leg2_lift != lift_tick[2]
