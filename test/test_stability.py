"""
Tests for the static stability primitive (plan U1).

These pin the geometry against hand-computed known cases before any gait depends on
it -- the body-frame composition and SSM are net-new and easy to get wrong. See
src/motion/stability.py.
"""

import numpy as np
import pytest

from src.motion import stability as S


# --- support_margin on known polygons ---------------------------------------

def test_square_margin_is_half_side_at_center():
    # unit-ish square centered at origin; COM at center -> margin = distance to a side
    feet = np.array([[1, 1], [-1, 1], [-1, -1], [1, -1]], dtype=float)
    m = S.support_margin(feet, stance=[0, 1, 2, 3], com_xy=(0.0, 0.0))
    assert m == pytest.approx(1.0)


def test_square_margin_shrinks_as_com_approaches_edge():
    feet = np.array([[1, 1], [-1, 1], [-1, -1], [1, -1]], dtype=float)
    m = S.support_margin(feet, stance=[0, 1, 2, 3], com_xy=(0.5, 0.0))
    assert m == pytest.approx(0.5)  # nearest edge is the right side x=1


def test_triangle_com_inside_positive():
    feet = np.array([[0, 0], [6, 0], [0, 6], [99, 99]], dtype=float)  # leg 3 lifted
    m = S.support_margin(feet, stance=[0, 1, 2], com_xy=(1.0, 1.0))
    assert m > 0


def test_triangle_com_on_edge_is_zero():
    feet = np.array([[0, 0], [6, 0], [0, 6]], dtype=float)
    # COM on the hypotenuse x+y=6
    m = S.support_margin(feet, stance=[0, 1, 2], com_xy=(3.0, 3.0))
    assert m == pytest.approx(0.0, abs=1e-9)


def test_triangle_com_outside_negative():
    feet = np.array([[0, 0], [6, 0], [0, 6]], dtype=float)
    m = S.support_margin(feet, stance=[0, 1, 2], com_xy=(5.0, 5.0))  # beyond hypotenuse
    assert m < 0


def test_collinear_support_is_degenerate():
    feet = np.array([[0, 0], [1, 0], [2, 0]], dtype=float)  # a line
    m = S.support_margin(feet, stance=[0, 1, 2], com_xy=(1.0, 0.0))
    assert m == float("-inf")


def test_margin_sign_independent_of_stance_ordering():
    feet = np.array([[0, 0], [6, 0], [0, 6]], dtype=float)
    a = S.support_margin(feet, stance=[0, 1, 2], com_xy=(1.0, 1.0))
    b = S.support_margin(feet, stance=[2, 0, 1], com_xy=(1.0, 1.0))
    assert a == pytest.approx(b)


# --- incenter ---------------------------------------------------------------

def test_incenter_of_345_right_triangle():
    inc = S.incenter([0, 0], [3, 0], [0, 4])  # inradius 1 -> incenter (1,1)
    assert inc == pytest.approx([1.0, 1.0])


def test_incenter_maximizes_minimum_edge_distance():
    tri = np.array([[0, 0], [3, 0], [0, 4]], dtype=float)
    inc = S.incenter(*tri)
    m_in = S.support_margin(tri, stance=[0, 1, 2], com_xy=inc)
    # any nearby interior point has a smaller minimum edge distance
    for dx, dy in [(0.3, 0), (-0.3, 0), (0, 0.3), (0, -0.3)]:
        m_off = S.support_margin(tri, stance=[0, 1, 2], com_xy=inc + np.array([dx, dy]))
        assert m_off < m_in + 1e-9


# --- body-frame composition -------------------------------------------------

def test_hip_corners_match_leg_map():
    corners = S.hip_corners(width=142, length=223)
    # 0=FL front-left, 1=FR front-right, 2=BR back-right, 3=BL back-left
    assert corners[0] == pytest.approx([111.5, -71.0])
    assert corners[1] == pytest.approx([111.5, 71.0])
    assert corners[2] == pytest.approx([-111.5, 71.0])
    assert corners[3] == pytest.approx([-111.5, -71.0])


def test_identical_per_leg_offsets_land_at_distinct_corners():
    # every leg commanded the same per-leg foot position...
    positions = np.tile([0.0, 0.0, 113.0], (4, 1))
    feet = S.body_frame_feet(positions, width=142, length=223)
    # ...yet they are physically at the four distinct body corners
    assert feet.shape == (4, 2)
    assert not np.allclose(feet[0], feet[2])
    # front-left vs back-right are ~ full diagonal apart
    diag = np.hypot(223, 142)
    assert np.hypot(*(feet[0] - feet[2])) == pytest.approx(diag)


def test_body_frame_adds_offset_to_corner():
    positions = np.array([[10, 5, 113], [0, 0, 113], [0, 0, 113], [0, 0, 113]], float)
    feet = S.body_frame_feet(positions, width=142, length=223)
    assert feet[0] == pytest.approx([111.5 + 10, -71.0 + 5])


def test_full_stance_square_is_stable_at_center():
    # nominal crouched stance: all feet at per-leg [0,0,z] -> body-frame corners,
    # COM at center -> comfortably inside, margin = half the smaller dimension
    positions = np.tile([0.0, 0.0, 113.0], (4, 1))
    feet = S.body_frame_feet(positions, width=142, length=223)
    m = S.support_margin(feet, stance=[0, 1, 2, 3], com_xy=(0.0, 0.0))
    assert m == pytest.approx(71.0)  # nearest edges are the long sides at y=±71
