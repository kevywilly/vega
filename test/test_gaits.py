"""
Gait behavior harness — locks in the CURRENT behavior of the production gait
iterators before the planned gait-core refactor (see
docs/ideation/2026-05-30-gait-stability-ideation.md, items 2-4).

These are characterization + invariant tests, not aspirational ones:
- The invariants (reachability, periodicity, frame contract, bounded step delta)
  hold for the current code and MUST keep holding through the refactor.
- The characterization test pins the current per-gait "load-bearing skid" (a
  planted foot resetting horizontally in one step). This is a *systemic*
  artifact of the `build_steps` construction — present in trot/sidestep/turn,
  not just prowl — so it is recorded, not asserted away.
- One xfail encodes the TARGET for the prowl rebuild (Goal 3): a slow, two-feet-
  down gait must not skid a planted foot. Trot tolerates the same skid because it
  is fast and diagonally supported; prowl does not. When the rebuild lands, that
  test flips to xpass and tells us.

Gaits are constructed exactly as `controller._get_gait_factory` builds them, so
the tests exercise the real production configurations.
"""

import numpy as np
import pytest
from dataclasses import replace

from settings import settings
from src.motion.kinematics import QuadrupedKinematics
from src.motion.gaits.trot import Trot
from src.motion.gaits.turn import Turn
from src.motion.gaits.prowl import Prowl
from src.motion.gaits.simplified_gait import SimpleTrotWithLateral, SimpleSidestep

_km = QuadrupedKinematics(
    settings.coxa_length,
    settings.femur_length,
    settings.tibia_length,
    settings.robot_width,
    settings.robot_length,
)

# name -> thunk returning a FRESH gait (gaits are stateful iterators, so every
# test must build its own). Mirrors controller._get_gait_factory.
GAITS = {
    "trot_fwd": lambda: SimpleTrotWithLateral(
        p0=settings.position_trot + settings.position_forward_offsets,
        params=settings.trot_params,
    ),
    "trot_in_place": lambda: Trot(params=settings.trot_in_place_params),
    "sidestep_R": lambda: SimpleSidestep(params=settings.sidestep_params),
    "sidestep_L": lambda: SimpleSidestep(
        params=replace(settings.sidestep_params, is_reversed=True)
    ),
    "turn_L": lambda: Turn(params=replace(settings.turn_params, turn_direction=1)),
    "turn_R": lambda: Turn(params=replace(settings.turn_params, turn_direction=-1)),
    "prowl": lambda: Prowl(p0=settings.position_prowl, params=settings.prowl_params),
}

GAIT_NAMES = list(GAITS)


def _cycle(gait, periods=1):
    """Collect (T, 4, 3) foot positions over `periods` full cycles, plus the
    wrap frame (so diffs cover the cycle boundary)."""
    n = gait.max_index
    frames = [np.asarray(next(gait), dtype=float) for _ in range(periods * n + 1)]
    return np.array(frames)


def _load_bearing_horizontal_skid(gait):
    """Max single-step horizontal (x,y) displacement of a foot that is planted
    (at/below stance height) on BOTH endpoints of the step — i.e. a foot that
    should be anchoring the body but instead jumps. Returns mm."""
    n = gait.max_index
    p0z = np.asarray(gait.p0, dtype=float)[:, 2]
    fr = _cycle(gait, periods=2)
    offz = fr[:, :, 2] - p0z[None, :]          # >=0 means foot at/below stance (loaded)
    horiz = fr[:, :, :2]
    dh = np.linalg.norm(np.diff(horiz, axis=0), axis=2)   # (T-1, 4)
    planted = (offz[:-1] >= -0.5) & (offz[1:] >= -0.5)
    loaded = np.where(planted, dh, np.nan)
    return float(np.nanmax(loaded)) if np.any(planted) else 0.0


# Current load-bearing skid maxima (mm), measured 2026-05-30. Ceilings sit just
# above each so the test GUARDS AGAINST REGRESSION (skid getting worse) while the
# recorded value documents today's reality. A refactor that reduces the skid still
# passes; one that worsens it fails.
SKID_CEILING_MM = {
    "trot_fwd": 60.0,       # measured 55
    "trot_in_place": 5.0,   # measured 0 (no translation)
    "sidestep_R": 35.0,     # measured 30
    "sidestep_L": 35.0,     # measured 30
    "turn_L": 75.0,         # measured 70
    "turn_R": 75.0,         # measured 70
    "prowl": 45.0,          # measured 40 -- the Goal-3 teleport
}

# No foot should translate more than this in a single controller step, for any
# gait. Current worst case is turn at 70mm; this cap catches gross regressions
# (e.g. a sign flip or bad roll) without being tight enough to fail today.
MAX_STEP_DELTA_MM = 80.0


@pytest.mark.parametrize("name", GAIT_NAMES)
def test_frame_contract(name):
    """Every yielded position is a finite (4, 3) array in mm."""
    gait = GAITS[name]()
    for _ in range(gait.max_index):
        frame = np.asarray(next(gait), dtype=float)
        assert frame.shape == (4, 3), f"{name}: bad frame shape {frame.shape}"
        assert np.all(np.isfinite(frame)), f"{name}: non-finite foot position"


@pytest.mark.parametrize("name", GAIT_NAMES)
def test_all_feet_reachable_through_cycle(name):
    """INVARIANT: every foot, every step, stays inside the leg's reach envelope.
    Must hold through the refactor — an unreachable target silently saturates IK."""
    gait = GAITS[name]()
    frames = _cycle(gait, periods=1)
    for t, frame in enumerate(frames):
        for leg in range(4):
            assert _km.validate_position(frame[leg]), (
                f"{name}: leg {leg} unreachable at step {t}: {frame[leg]}"
            )


@pytest.mark.parametrize("name", GAIT_NAMES)
def test_gait_is_periodic(name):
    """INVARIANT: the gait closes — the pose after `max_index` steps equals the
    starting pose. Catches a refactor that breaks cyclic continuity."""
    gait = GAITS[name]()
    start = np.asarray(next(gait), dtype=float)
    for _ in range(gait.max_index - 1):
        next(gait)
    wrap = np.asarray(next(gait), dtype=float)
    assert np.allclose(start, wrap), f"{name}: not periodic over max_index steps"


@pytest.mark.parametrize("name", GAIT_NAMES)
def test_step_delta_bounded(name):
    """INVARIANT (loose): no foot teleports more than MAX_STEP_DELTA_MM in one
    step. Gross-regression guard, not a smoothness assertion."""
    gait = GAITS[name]()
    frames = _cycle(gait, periods=1)
    deltas = np.linalg.norm(np.diff(frames, axis=0), axis=2)
    worst = float(deltas.max())
    assert worst <= MAX_STEP_DELTA_MM, (
        f"{name}: foot moved {worst:.1f}mm in one step (cap {MAX_STEP_DELTA_MM})"
    )


@pytest.mark.parametrize("name", GAIT_NAMES)
def test_load_bearing_skid_characterization(name):
    """CHARACTERIZATION: pins the current planted-foot horizontal skid per gait.
    This documents the systemic `build_steps` foot-reset (see module docstring)
    and guards against it getting worse during the refactor."""
    skid = _load_bearing_horizontal_skid(GAITS[name]())
    assert skid <= SKID_CEILING_MM[name], (
        f"{name}: load-bearing skid {skid:.1f}mm exceeds recorded ceiling "
        f"{SKID_CEILING_MM[name]}mm -- behavior regressed"
    )


@pytest.mark.xfail(
    reason="Goal 3: prowl is a slow, two-feet-down gait, so its ~40mm planted-foot "
    "reset (inherited from the trot build_steps construction) is not dynamically "
    "rescued and reads as a skid/teleport. The rebuild as a static wave gait with a "
    "body-shift sub-phase should drop load-bearing skid to a smooth stride drag. "
    "When that lands this xpasses. (Trot/sidestep share the artifact but tolerate it.)",
    strict=False,
)
def test_prowl_planted_feet_do_not_skid():
    """TARGET for the prowl rebuild: a planted foot should only drag smoothly as
    the body advances (~stride/num_steps per step), never reset a full stride."""
    skid = _load_bearing_horizontal_skid(GAITS["prowl"]())
    assert skid <= 15.0, f"prowl planted foot skids {skid:.1f}mm/step (target <=15)"
