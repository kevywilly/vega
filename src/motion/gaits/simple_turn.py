"""SimpleTurn -- a minimal, scrub-free in-place turn.

The legacy `Turn` (turn.py) fakes a yaw by translating every foot along a
straight **lateral (y) line** (legs 2,3 negated) and dragging all four planted
feet back together in a final shared segment. A foot at radius r moving on a
straight line is a *chord*, never the arc the body actually rotates through --
that mismatch is the documented scrub (GAITS.md, settings.yml NOTE).

SimpleTurn keeps the proven trot *structure* (diagonal pairs, smooth sin lift)
but swaps linear stride for a genuine **rotation about the body centre**: each
foot's offset is `R_z(angle) . r_i - r_i`, where `r_i` is the foot's neutral
position relative to the body centre. Because the planted foot now follows its
true arc, the body can yaw underneath it without the contact point sliding --
scrub-free by construction (the residual is only step discretisation).

This is the deliberately small experiment; see arc_turn.py for the ICR /
continuous-phase version. The legacy `Turn` is left untouched (its migration
tests pin it byte-for-byte).
"""

import numpy as np

from settings import settings
from src.motion import stability
from src.motion.gaits.gait import Gait
from src.motion.gaits.gait_spec import GaitSpec, LegSpec, compile_spec
from src.motion.gaits import trajectories as T


def _const(arr):
    """A GaitSpec trajectory callable returning a fixed per-leg array. Each leg
    rotates about the body centre by the same angle schedule but from its own
    radius r_i, so the four legs need distinct, explicit offset arrays (no single
    phase-offset weld fits -- same reasoning as legacy Turn)."""
    return lambda _n: arr


class SimpleTurn(Gait):
    """In-place yaw built as a diagonal trot whose feet rotate (not translate).

    Diagonal pairs {0,2} and {1,3} swing a half-cycle apart. Within a cycle a
    foot lifts and rotates forward in the turn direction (swing), then rotates
    the other way while planted (stance) -- and the planted rotation, following
    the foot's arc about the body centre, is what yaws the body.

    `turn_direction` sets the sense; `is_reversed` flips it via the stride sign.
    """

    def build_steps(self):
        self.steps = compile_spec(self._spec())

    # --- geometry -----------------------------------------------------------
    def _foot_radii(self) -> np.ndarray:
        """Each foot's neutral (x, y) position relative to the body centre.

        Body centre is the chassis origin; hips sit at the four corners
        (+/- length/2, +/- width/2) for leg order [FL, FR, BR, BL] (X forward,
        Y left -- see CLAUDE.md leg layout). The neutral foot is that hip plus
        the leg-frame ready position `p0[i]` (leg and body frames share
        orientation, so the corner offset just recentres it on the body).

        Note: scrub-freeness does not depend on getting this exactly right --
        any consistent r_i yields a planted foot that tracks its own arc. The
        corner term mainly sets *where* the rotation centre lands; corners
        dominate (~111, ~71 mm) over the foot's own xy, so the spin centres
        close to the chassis centre.

        Uses stability.hip_corners() -- the codebase's single source of truth for
        the body-frame hip geometry (matches the kinematics corner-sign pattern),
        the same composer prowl uses.
        """
        return stability.hip_corners() + np.asarray(self.p0, dtype=float)[:, :2]

    def _spec(self) -> GaitSpec:
        num = self.num_steps
        period = num * 4
        direction = self.turn_direction * (-1 if self.is_reversed else 1)
        clearance = self.clearance

        radii = self._foot_radii()                       # (4, 2)
        rmean = float(np.hypot(radii[:, 0], radii[:, 1]).mean())
        # Map the configured linear stride (mm) onto a yaw amplitude (rad) at the
        # mean foot radius, so `stride` keeps its familiar "how far per step" feel.
        amp = (self.stride / rmean) if rmean else 0.0

        # Angle schedule over one cycle, mirroring trot's x-shape: rise to +amp
        # while swinging, settle to 0, then sweep to -amp while planted (the push).
        angle = np.hstack([
            T.stride_forward(num),   # 0 -> 1  (lift + rotate forward)
            T.stride_home(num),      # 1 -> 0
            T.stride_back(num * 2),  # 0 -> -1 (planted push)
        ]) * amp * direction
        # Lift only during the swing segment (sin arch, zero at lift-off/touch-down).
        lift = np.hstack([T.lift(num), T.zero(num * 3)]) * (-clearance)

        legs = []
        for i in range(4):
            rx, ry = radii[i]
            ca, sa = np.cos(angle), np.sin(angle)
            # R_z(angle) . r_i - r_i, per axis, as a function of cycle index.
            dx = (ca * rx - sa * ry) - rx
            dy = (sa * rx + ca * ry) - ry
            # Diagonal pair {1,3} runs a half-cycle later.
            roll = (num * 2) if (i % 2 == 1) else 0
            xs = np.roll(dx, roll)
            ys = np.roll(dy, roll)
            zs = np.roll(lift, roll)
            legs.append(LegSpec(x=_const(xs), y=_const(ys), z=_const(zs)))

        return GaitSpec(period=period, duty_factor=0.75, legs=legs)


if __name__ == "__main__":
    gait = SimpleTurn(p0=settings.position_ready, params=settings.turn_params)
    gait.plotit()
