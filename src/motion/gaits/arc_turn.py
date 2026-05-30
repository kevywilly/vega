"""ArcTurn -- the ambitious turn: continuous-phase, ICR-parameterised, world-frame planting.

Where SimpleTurn (simple_turn.py) is "trot, but the feet rotate", ArcTurn is a
small step toward the unified locomotion model the ideation surfaced:

  * Continuous phase clock -- positions are computed on demand each tick from a
    float phase, not replayed from a precomputed int-truncated step array. Turn
    rate is a live parameter; there is no step_size quantisation.

  * Instantaneous Centre of Rotation (ICR) -- every foot rotates about a single
    point. ICR at the body centre => spin in place; ICR offset to the side =>
    an arc turn (curving path). `pivot_ratio` (a param that exists in GaitParams
    but the legacy gaits never used) shifts the ICR fore/aft.

  * World-frame stance planting -- a planted foot is rotated rigidly about the
    ICR by exactly -d_psi each tick, where d_psi is the body's yaw increment.
    The contact point therefore never moves in the world: scrub is impossible by
    construction, not merely reduced by finer sampling.

  * Smooth swing -- lift follows a sin arch (zero vertical velocity at lift-off
    and touch-down) and the horizontal reposition uses a smoothstep ease, so the
    foot is never dragged onto the ground.

It overrides `__next__` to act as a pure generator; `self.steps` is set to a
neutral frame only to satisfy the base-class contract. The legacy `Turn` is left
untouched.
"""

import numpy as np

from settings import settings
from src.motion import stability
from src.motion.gaits.gait import Gait


def _smoothstep(s: float) -> float:
    """C1 ease 3s^2 - 2s^3, zero slope at both ends -> no horizontal jerk at
    touch-down."""
    s = min(max(s, 0.0), 1.0)
    return s * s * (3.0 - 2.0 * s)


def _rot(v, a):
    """Rotate a 2-vector by angle a about the origin."""
    c, s = np.cos(a), np.sin(a)
    return np.array([c * v[0] - s * v[1], s * v[0] + c * v[1]])


class ArcTurn(Gait):
    """Continuous ICR turn. Diagonal pairs {0,2}/{1,3} a half-cycle apart.

    Tunables (all with sane defaults; this is a play/experiment gait):
      * yaw_per_cycle  -- body yaw (rad) per full cycle; sign = turn direction.
                          Derived from `stride` for parity with the other gaits.
      * icr            -- (x, y) of the rotation centre in the body frame.
                          (0, 0) spins in place; non-zero curves the path.
      * swing_frac     -- fraction of each leg's cycle spent in swing (duty = 1 - this).
    """

    SWING_FRAC = 0.25  # duty factor 0.75 -> >=3 feet down most of the cycle

    def build_steps(self):
        # Geometry: each foot's neutral xy relative to the body centre, via the
        # codebase's single source of truth (matches kinematics corner signs).
        p0 = np.asarray(self.p0, dtype=float)
        self._neutral_xy = stability.hip_corners() + p0[:, :2]   # (4, 2) body-frame feet
        rmean = float(np.hypot(self._neutral_xy[:, 0], self._neutral_xy[:, 1]).mean())

        direction = self.turn_direction * (-1 if self.is_reversed else 1)
        # Per-cycle yaw, scaled from the familiar linear `stride` knob.
        self._yaw_per_cycle = (2.0 * self.stride / rmean if rmean else 0.0) * direction

        # ICR: centre by default; pivot_ratio shifts it fore/aft (0.5 = centre).
        self._icr = np.array([(self.pivot_ratio - 0.5) * settings.robot_length, 0.0])

        # Continuous-phase state.
        self._N = max(self.num_steps * 4, 1)              # ticks per cycle
        self._dpsi = self._yaw_per_cycle / self._N        # yaw increment per tick
        self._phi = 0.0
        self._psi = 0.0                                   # accumulated body yaw
        self._phase_offset = np.array([0.0, 0.5, 0.0, 0.5])  # diagonal pairs
        # Live foot positions (body frame, xy) and per-leg swing bookkeeping.
        self._foot_xy = self._neutral_xy.copy()
        self._was_swing = np.array([False, False, False, False])
        self._lift_off = self._neutral_xy.copy()
        self._target = self._neutral_xy.copy()

        # Satisfy the base contract: a single neutral frame (we override __next__).
        self.steps = np.zeros((4, 1, 3))

    # ArcTurn is a generator; ignore the indexed-array hot path entirely.
    def __next__(self):
        out = np.array(self.p0, dtype=float)
        stance_frac = 1.0 - self.SWING_FRAC

        for i in range(4):
            lp = (self._phi + self._phase_offset[i]) % 1.0
            swinging = lp < self.SWING_FRAC

            if swinging:
                s = lp / self.SWING_FRAC
                if not self._was_swing[i]:
                    # Lift-off: remember where we leave, and where to land. The
                    # foot must be replaced forward by the arc it will sweep back
                    # during the coming stance, so the cycle stays periodic.
                    self._lift_off[i] = self._foot_xy[i].copy()
                    advance = stance_frac * self._yaw_per_cycle
                    self._target[i] = self._icr + _rot(self._lift_off[i] - self._icr, advance)
                ease = _smoothstep(s)
                xy = (1.0 - ease) * self._lift_off[i] + ease * self._target[i]
                z = self.clearance * np.sin(np.pi * s)
                self._foot_xy[i] = xy
            else:
                # Stance: rotate rigidly about the ICR by -d_psi so the contact
                # point stays fixed in the world while the body yaws +d_psi.
                self._foot_xy[i] = self._icr + _rot(self._foot_xy[i] - self._icr, -self._dpsi)
                z = 0.0

            self._was_swing[i] = swinging
            # Emit as an offset from the leg-frame neutral (p0 + body-frame delta).
            out[i, 0] = self.p0[i][0] + (self._foot_xy[i][0] - self._neutral_xy[i][0])
            out[i, 1] = self.p0[i][1] + (self._foot_xy[i][1] - self._neutral_xy[i][1])
            out[i, 2] = self.p0[i][2] - z

        self._phi += 1.0 / self._N
        self._psi += self._dpsi
        if self._phi >= 1.0:
            self._phi -= 1.0
        self.positions = out
        return out

    def degrees_per_cycle(self) -> float:
        """How far the body yaws per full cycle -- the gait is commandable:
        'turn 90 deg' == run ceil(90 / this) cycles."""
        return float(np.degrees(self._yaw_per_cycle))


if __name__ == "__main__":
    gait = ArcTurn(p0=settings.position_ready, params=settings.turn_params)
    print(f"yaw/cycle = {gait.degrees_per_cycle():.1f} deg, ticks/cycle = {gait._N}")
    for _ in range(gait._N):
        next(gait)
    gait_again = ArcTurn(p0=settings.position_ready, params=settings.turn_params)
    gait_again.plotit()
