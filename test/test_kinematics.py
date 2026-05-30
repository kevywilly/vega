"""
Kinematics tests — the guardrail for the IK/FK math.

Key invariant: forward_kinematics is a true inverse of inverse_kinematics for ANY
lateral offset (y != 0). This is what catches regressions in the radial reach
(r = sqrt(y^2 + z^2)) and the coxa rotation in FK. See docs/solutions/ for context.
"""

import numpy as np
import pytest

from settings import settings
from src.motion.kinematics import QuadrupedKinematics

_km = QuadrupedKinematics(
    settings.coxa_length,
    settings.femur_length,
    settings.tibia_length,
    settings.robot_width,
    settings.robot_length,
)

# Foot positions across the working envelope. z is POSITIVE at stance in this codebase.
# Includes pure-vertical (trot) and large lateral offsets (sidestep / prowl / body-shift),
# the regime where the old z-instead-of-radial bug placed feet up to ~30mm off.
REACHABLE = [
    [0, 0, 151],
    [100, 0, 151],
    [-80, 0, 140],
    [100, 40, 151],
    [100, -60, 151],
    [80, 90, 120],
    [0, 30, 151],
    [-50, -45, 130],
]


@pytest.mark.parametrize("pos", REACHABLE)
def test_ik_fk_round_trip(pos):
    """FK(IK(pos)) == pos for any lateral offset — the core correctness guardrail."""
    p = np.array(pos, dtype=float)
    angles = _km.inverse_kinematics(p)
    back = _km.forward_kinematics(angles)
    assert np.allclose(back, p, atol=1e-6), f"round-trip drift: {p} -> {back}"


@pytest.mark.parametrize("pos", REACHABLE)
def test_vectorized_ik_matches_scalar(pos):
    """The production vectorized IK must equal the scalar reference for every leg."""
    p = np.array(pos, dtype=float)
    scalar = _km.inverse_kinematics(p)
    vectorized = _km.inverse_kinematics_vectorized(np.tile(p, (4, 1)))
    assert np.allclose(vectorized, scalar, atol=1e-9)


@pytest.mark.parametrize("pos", [[60, 0, 151], [60, 0, 120], [40, 0, 90], [0, 0, 200]])
def test_trot_regime_unchanged_at_y_zero(pos):
    """At y=0 the radial fix is a no-op (r == z), so trot is bit-for-bit unaffected
    and FK reports y == 0 exactly."""
    p = np.array(pos, dtype=float)
    back = _km.forward_kinematics(_km.inverse_kinematics(p))
    assert back[1] == pytest.approx(0.0, abs=1e-9)
    assert np.allclose(back, p, atol=1e-6)


def test_large_lateral_offset_is_accurate():
    """Regression: a foot commanded with large lateral y lands within 0.01mm
    (the pre-fix error here was ~30mm)."""
    p = np.array([80.0, 90.0, 120.0])
    back = _km.forward_kinematics(_km.inverse_kinematics(p))
    assert np.linalg.norm(back - p) < 1e-2


def test_reachability_bounds():
    assert _km.validate_position(np.array([0, 0, 151]))       # mid-envelope
    assert not _km.validate_position(np.array([0, 0, 300]))   # beyond femur+tibia (216)
    assert not _km.validate_position(np.array([0, 0, 5]))      # inside min reach (12)
