"""
Static stability geometry: body-frame foot composition, support polygon, and
static stability margin (SSM).

This is the offline stability primitive for the static wave gait (see
docs/plans/2026-05-30-002-feat-prowl-wave-gait-plan.md). It answers one question:
given the four commanded foot positions and which legs are on the ground, does the
robot's center of mass project inside the support polygon, and by how much?

THE LOAD-BEARING SUBTLETY: gait foot positions are in PER-LEG frame -- each foot is
measured from its own leg's femur pivot, and `position_*` is identical for every
leg (e.g. [0,0,113]). Two feet at the same per-leg coordinate are physically ~width
or ~length apart. A support polygon is meaningless in per-leg coordinates, so this
module first composes the feet into a single BODY frame by adding each leg's
hip-mount corner offset (derived from robot_width/length and the leg map
0=FL,1=FR,2=BR,3=BL). Nothing else in the codebase does this.

Conventions (body frame): X forward, Y to the right, Z up (matches GAITS.md). The
support polygon lives in the X-Y ground plane; Z is the vertical/contact axis and is
ignored here. The gait's +x already means "foot forward" (the IK x-inversion is
internal to the servo mapping), so no extra inversion is applied at this layer. COM
is the body geometric center (origin), plus an optional calibrated static offset --
the CHAMP/spotMicro pattern, not sensing.
"""

from __future__ import annotations

import numpy as np

from settings import settings

# Leg map 0=FL, 1=FR, 2=BR, 3=BL. Corner sign pattern matches apply_body_tilt's
# yaw [1,1,-1,-1] (front/back) and pitch [1,-1,-1,1] (left/right) in kinematics.py.
_CORNER_SIGNS = np.array([
    [+1, -1],   # 0 front-left
    [+1, +1],   # 1 front-right
    [-1, +1],   # 2 back-right
    [-1, -1],   # 3 back-left
], dtype=float)


def hip_corners(width: float | None = None, length: float | None = None) -> np.ndarray:
    """Body-frame XY of the four hip mounts (femur pivots), shape (4, 2).

    Defaults to the robot's configured dimensions; overridable for tests."""
    w = (settings.robot_width if width is None else width) / 2.0
    length_ = (settings.robot_length if length is None else length) / 2.0
    return _CORNER_SIGNS * np.array([length_, w])


def body_frame_feet(
    positions: np.ndarray, width: float | None = None, length: float | None = None
) -> np.ndarray:
    """Compose per-leg foot positions into body-frame ground-plane XY, shape (4, 2).

    `positions` is the (4, 3) commanded foot positions (p0 + gait offsets) in per-leg
    frame; only x (forward) and y (right) are used. Each leg's foot is placed relative
    to its hip-mount corner."""
    positions = np.asarray(positions, dtype=float)
    return hip_corners(width, length) + positions[:, :2]


def convex_hull(points: np.ndarray) -> np.ndarray:
    """Counter-clockwise convex hull (Andrew's monotone chain). Returns the hull
    vertices, shape (k, 2). For <3 unique points returns them as-is (degenerate)."""
    pts = np.asarray(points, dtype=float)
    uniq = sorted({(float(p[0]), float(p[1])) for p in pts})
    if len(uniq) <= 2:
        return np.array([list(p) for p in uniq], dtype=float)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in uniq:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(uniq):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    return np.array(hull, dtype=float)  # CCW winding


def com_projection(offset=(0.0, 0.0)) -> np.ndarray:
    """COM ground projection in body frame: geometric center (origin) plus an
    optional calibrated static offset (e.g. for a rear-mounted battery)."""
    return np.array(offset, dtype=float)


def support_margin(feet_xy: np.ndarray, stance: "list[int] | np.ndarray",
                   com_xy=(0.0, 0.0)) -> float:
    """Static stability margin: signed distance from the COM projection to the
    nearest edge of the support polygon (convex hull of the stance feet).

    Positive => COM inside the polygon (stable), and the value is the tip-over
    distance to the closest edge. Zero => on an edge. Negative => COM outside
    (falling). A degenerate support (fewer than 3 non-collinear stance feet) returns
    -inf: there is no area to be statically stable over.
    """
    feet_xy = np.asarray(feet_xy, dtype=float)
    pts = feet_xy[list(stance)]
    com = np.asarray(com_xy, dtype=float)
    hull = convex_hull(pts)
    if len(hull) < 3:
        return float("-inf")
    n = len(hull)
    dmin = np.inf
    for i in range(n):
        a = hull[i]
        b = hull[(i + 1) % n]
        e = b - a
        length = np.hypot(e[0], e[1])
        # signed perpendicular distance; CCW hull => interior is to the left => positive
        d = (e[0] * (com[1] - a[1]) - e[1] * (com[0] - a[0])) / length
        dmin = min(dmin, d)
    return float(dmin)


def incenter(a, b, c) -> np.ndarray:
    """Incenter of triangle ABC -- the point that maximizes the minimum distance to
    the three edges (the most stability-robust COM target for the support triangle).
    Weighted by the lengths of the opposite sides."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    c = np.asarray(c, float)
    la = np.hypot(*(b - c))   # opposite a
    lb = np.hypot(*(a - c))   # opposite b
    lc = np.hypot(*(a - b))   # opposite c
    return (la * a + lb * b + lc * c) / (la + lb + lc)
