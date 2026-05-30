import numpy as np

from src.motion.gaits.gait import Gait
from src.motion.gaits.gait_spec import GaitSpec, LegSpec, compile_spec
from src.motion.gaits import trajectories as T


def _const(arr):
    """A trajectory callable that returns a fixed per-leg array (turn's phasing is
    baked into explicit per-leg trajectories, not a uniform phase offset)."""
    return lambda _n: arr


class Turn(Gait):
    """In-place turn: a 5-segment cycle in which each leg lifts and steps laterally
    in its own segment (legs 0 -> 1 -> 2 -> 3), then all feet return laterally
    together in the final segment. A genuine 4-independent-leg gait, expressed as
    four explicit per-leg LegSpecs -- no single phase offset fits this shape.

    turn_direction sets the rotation sense; is_reversed flips it via the stride sign.
    See docs/plans/2026-05-30-001-refactor-gait-core-phasing-plan.md.
    """

    def build_steps(self):
        self.steps = compile_spec(self._spec())

    def _spec(self) -> GaitSpec:
        num = self.num_steps
        mag_y = -self.stride
        mag_z = -self.clearance
        direction = self.turn_direction

        step = T.stride_forward(num) * mag_y * direction   # lateral out (while lifted)
        back = T.stride_home(num) * mag_y * direction       # lateral return (planted)
        lift = T.updown(num, fast=False) * mag_z            # full sin-arch lift
        o = T.zero(num)                                     # an idle segment

        # Each leg lifts/steps in its own segment; legs 2,3 step the opposite lateral
        # sense (-step); every leg shares the lateral return in the final segment.
        ys = [
            np.hstack([step, o, o, o, back]),
            np.hstack([o, step, o, o, back]),
            np.hstack([o, o, -step, o, back]),
            np.hstack([o, o, o, -step, back]),
        ]
        zs = [
            np.hstack([lift, o, o, o, o]),
            np.hstack([o, lift, o, o, o]),
            np.hstack([o, o, lift, o, o]),
            np.hstack([o, o, o, lift, o]),
        ]
        legs = [LegSpec(y=_const(ys[i]), z=_const(zs[i])) for i in range(4)]
        return GaitSpec(period=num * 5, duty_factor=0.8, legs=legs)
