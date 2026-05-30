"""
Tests for the generalized gait core (plan U2).

U2 replaces the steps1..steps4 special-casing in `get_offsets` with a single
canonical `self.steps : (4, N, 3)` indexed per leg. These tests lock the
architectural invariants:

- `self.steps` is always (4, N, 3) and `get_offsets` is a plain index into it.
- The diagonal weld ({0,2} / {1,3}) is preserved for legacy 2-group gaits and the
  4-independent-leg path (Turn) keeps distinct legs.
- `build_steps` may set `self.steps` directly (the forward path for U3 GaitSpec
  gaits), bypassing the steps1..4 assembly.

Byte-equality of full-cycle output vs. the pre-refactor baseline is enforced by
test/test_gaits.py (unchanged characterization of all 7 production configs); this
file covers the new structure those tests don't name directly.
"""

import numpy as np
import pytest
from dataclasses import replace

from settings import settings
from src.motion.gaits.gait import Gait
from src.motion.gaits.trot import Trot
from src.motion.gaits.turn import Turn
from src.motion.gaits.prowl import Prowl
from src.motion.gaits.simplified_gait import SimpleTrotWithLateral, SimpleSidestep

# Production gait configs, built exactly as controller._get_gait_factory builds them.
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

# Gaits that weld diagonal pairs (legs 2,3 mirror 0,1) vs. true 4-independent legs.
# prowl is now the static wave gait -- four independently-phased legs, not welded.
WELDED = ["trot_fwd", "trot_in_place", "sidestep_R", "sidestep_L"]
INDEPENDENT = ["turn_L", "turn_R", "prowl"]


@pytest.mark.parametrize("name", GAIT_NAMES)
def test_steps_is_4xNx3(name):
    g = GAITS[name]()
    assert g.steps.shape == (4, g.max_index, 3)
    assert g.steps.shape[1] == g.max_index


@pytest.mark.parametrize("name", GAIT_NAMES)
def test_get_offsets_is_a_plain_index_into_steps(name):
    g = GAITS[name]()
    for i in range(g.max_index):
        assert np.array_equal(g.get_offsets(i), g.steps[:, i])


@pytest.mark.parametrize("name", WELDED)
def test_welded_gaits_mirror_diagonal_pairs(name):
    g = GAITS[name]()
    assert np.array_equal(g.steps[0], g.steps[2]), "leg 2 must mirror leg 0"
    assert np.array_equal(g.steps[1], g.steps[3]), "leg 3 must mirror leg 1"


@pytest.mark.parametrize("name", INDEPENDENT)
def test_independent_gaits_have_distinct_legs(name):
    g = GAITS[name]()
    welded = np.array_equal(g.steps[0], g.steps[2]) and np.array_equal(
        g.steps[1], g.steps[3]
    )
    assert not welded, "a 4-independent-leg gait should not weld diagonal pairs"


def test_shape_and_size_reference_canonical_steps():
    g = GAITS["trot_fwd"]()
    assert g.shape == g.steps[0].shape == (g.max_index, 3)
    assert g.size == g.steps[0].size


# --- _assemble_steps and the direct-set path (synthetic minimal gaits) -------

class _TwoGroup(Gait):
    """Sets only steps1/steps2 -> should weld into [s1, s2, s1, s2]."""

    def build_steps(self):
        n = self.num_steps * 4
        base = Gait.reshape_steps(
            np.array([np.arange(n), np.zeros(n), np.zeros(n)]), n
        )
        self.steps1 = base
        self.steps2 = base + 100


class _FourLeg(Gait):
    """Sets all four step arrays -> should use [s1, s2, s3, s4] unchanged."""

    def build_steps(self):
        n = self.num_steps * 4
        base = Gait.reshape_steps(
            np.array([np.arange(n), np.zeros(n), np.zeros(n)]), n
        )
        self.steps1 = base
        self.steps2 = base + 100
        self.steps3 = base + 200
        self.steps4 = base + 300


class _DirectSteps(Gait):
    """Sets self.steps directly -> assembly is skipped (the U3 GaitSpec path)."""

    def build_steps(self):
        n = self.num_steps * 4
        self.steps = np.zeros((4, n, 3), dtype=int)
        self.steps[1] += 7


def test_assemble_welds_when_no_steps34():
    g = _TwoGroup()
    assert np.array_equal(g.steps, np.stack([g.steps1, g.steps2, g.steps1, g.steps2]))


def test_assemble_uses_all_four_when_steps34_set():
    g = _FourLeg()
    assert np.array_equal(g.steps, np.stack([g.steps1, g.steps2, g.steps3, g.steps4]))


def test_build_steps_may_set_canonical_steps_directly():
    g = _DirectSteps()
    n = g.num_steps * 4
    assert g.steps.shape == (4, n, 3)
    assert g.max_index == n
    assert np.array_equal(g.steps[1], np.full((n, 3), 7))
    # iteration still works through the canonical array
    frame = next(g)
    assert frame.shape == (4, 3)
    assert np.array_equal(frame, g.p0 + g.steps[:, 0])
