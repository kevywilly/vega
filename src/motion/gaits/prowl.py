"""
Prowl - static wave gait.

A statically stable, one-leg-at-a-time crawl. The cycle has 8 equal segments
alternating a body-shift with a single-leg swing:

    shift · swing L0 · shift · swing L2 · shift · swing L1 · shift · swing L3

so each leg is airborne for only 1/8 of the cycle (duty factor 7/8 -- McGhee's
"intermittent" wave gait, well above the 3/4 static-stability minimum) and three
feet are always planted. The lift sequence is LF -> RH -> RF -> LH (legs
0 -> 2 -> 1 -> 3), the canonical lateral-sequence walk.

Before each leg lifts, a shared body offset moves the COM toward the incenter of
the standing three-foot triangle (the point that maximizes the minimum distance to
the triangle's edges), so the COM projection stays comfortably inside the support
polygon throughout -- verified offline by the static-margin gate in
test/test_prowl_wave.py. Backward prowl is the same wave with negated stride.

This replaces the old diagonal-trot-coupled prowl that lifted two opposite feet at
once. See docs/plans/2026-05-30-002-feat-prowl-wave-gait-plan.md.
"""

import numpy as np

from src.motion.gaits.gait import Gait
from src.motion.gaits.gait_spec import GaitSpec, LegSpec, compile_spec
from src.motion.gaits import trajectories as T
from src.motion import stability

# Of the 8 segments, the index in which each leg swings. Lift sequence
# LF -> RH -> RF -> LH = legs 0 -> 2 -> 1 -> 3 at the four odd (swing) segments.
_SWING_SEGMENT = {0: 1, 2: 3, 1: 5, 3: 7}

# How far toward the support-triangle incenter to shift the COM (1.0 = all the way,
# maximum margin; lower trades margin for less body motion). Tuned to 0.4: SSM stays
# ~22 mm (comfortably positive) while planted-foot per-step motion stays ~12 mm,
# under the 15 mm skid target. Gated by the static-margin + skid tests.
_SHIFT_FRACTION = 0.4


class Prowl(Gait):
    """Static wave gait with a per-lift body shift. Drop-in for the controller's
    PROWL / PROWL_BACKWARD (same Gait(p0, params) constructor)."""

    SEGMENTS = 8

    def build_steps(self):
        self.steps = compile_spec(self._spec())

    def _spec(self) -> GaitSpec:
        num = self.num_steps
        stride, clearance = self.stride, self.clearance
        segs = self.SEGMENTS

        def base_x(_n):
            # place the foot forward while airborne (segment 0), then drag it back
            # smoothly over the seven stance segments -> net forward travel, no skid.
            swing = np.linspace(-stride / 2, stride / 2, num)
            drag = np.linspace(stride / 2, -stride / 2, num * (segs - 1))
            return np.hstack([swing, drag])

        def base_z(_n):
            # clean symmetric lift in the swing segment only (no downupdown press).
            return np.hstack([T.lift(num) * (-clearance), T.zero(num * (segs - 1))])

        legs = [
            LegSpec(x=base_x, z=base_z, phase_offset=_SWING_SEGMENT[i] / segs)
            for i in range(4)
        ]
        return GaitSpec(
            period=num * segs,
            duty_factor=(segs - 1) / segs,   # 7/8
            legs=legs,
            body=self._body_shift(num),
        )

    def _body_shift(self, num) -> np.ndarray:
        """Shared (N, 3) body offset. For each upcoming swing, target the incenter of
        the three standing feet; transition between targets during the shift segments
        and hold during the swing segments. Smooth (small per-step) so planted feet
        do not skid."""
        feet = stability.body_frame_feet(np.asarray(self.p0, dtype=float))  # nominal = corners
        # body offset that lands the COM near the standing triangle's incenter:
        # adding -incenter to every foot puts the COM (body origin) at the incenter.
        target = {}
        for leg in range(4):
            others = [j for j in range(4) if j != leg]
            inc = stability.incenter(feet[others[0]], feet[others[1]], feet[others[2]])
            target[leg] = -inc * _SHIFT_FRACTION

        order = [0, 2, 1, 3]                       # lift sequence
        b = [target[i] for i in order]             # target held during each swing
        # per-segment (start, end) XY: shift segments interpolate, swing segments hold
        seg_pts = [
            (b[3], b[0]),  # 0 shift -> L0
            (b[0], b[0]),  # 1 swing L0
            (b[0], b[1]),  # 2 shift -> L2
            (b[1], b[1]),  # 3 swing L2
            (b[1], b[2]),  # 4 shift -> L1
            (b[2], b[2]),  # 5 swing L1
            (b[2], b[3]),  # 6 shift -> L3
            (b[3], b[3]),  # 7 swing L3
        ]
        xs, ys = [], []
        for start, end in seg_pts:
            xs.append(np.linspace(start[0], end[0], num))
            ys.append(np.linspace(start[1], end[1], num))
        x = np.hstack(xs)
        y = np.hstack(ys)
        z = np.zeros(num * self.SEGMENTS)
        return np.column_stack([x, y, z])
