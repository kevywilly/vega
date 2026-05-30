"""Ad-hoc verification for the two new turn gaits vs the legacy Turn.

Checks: (1) they iterate without NaN, (2) feet trace ARCS (both x and y move),
unlike the legacy pure-lateral chord, (3) net yaw per cycle is sane, (4) planted
feet keep a ~constant radius from the rotation centre (scrub-free signature).
"""
import numpy as np
from settings import settings
from src.motion.gaits.turn import Turn
from src.motion.gaits.simple_turn import SimpleTurn
from src.motion.gaits.arc_turn import ArcTurn

np.set_printoptions(suppress=True, precision=2)


def collect(gait, n):
    frames = []
    for _ in range(n):
        frames.append(np.array(next(gait), dtype=float))
    return np.stack(frames)  # (n, 4, 3)


def report(name, gait, n, p0):
    frames = collect(gait, n)
    offs = frames - np.asarray(p0, dtype=float)  # per-leg offset from neutral
    nan = np.isnan(frames).any()
    # x/y travel per leg over the cycle
    dx = offs[:, :, 0].ptp(axis=0)
    dy = offs[:, :, 1].ptp(axis=0)
    dz = offs[:, :, 2].ptp(axis=0)
    print(f"\n=== {name} (frames={n}) ===")
    print(f"  NaN present : {nan}")
    print(f"  x travel/leg: {dx}")
    print(f"  y travel/leg: {dy}")
    print(f"  z travel/leg: {dz}")
    arc = (dx.min() > 1.0)  # any meaningful x motion => not a pure-Y chord
    print(f"  feet trace ARCS (x moves, not pure-Y chord): {arc}")
    return frames


N = 4 * int(90 / settings.turn_params.step_size)
p0 = settings.position_ready

print("legacy Turn step_size ->", settings.turn_params.step_size, "N=", N)
report("legacy Turn", Turn(p0=p0, params=settings.turn_params), N, p0)
report("SimpleTurn", SimpleTurn(p0=p0, params=settings.turn_params), N, p0)

at = ArcTurn(p0=p0, params=settings.turn_params)
print(f"\nArcTurn yaw/cycle = {at.degrees_per_cycle():.1f} deg")
report("ArcTurn", at, at._N, p0)

# Scrub signature for ArcTurn: a planted foot should hold ~constant radius from ICR.
at2 = ArcTurn(p0=p0, params=settings.turn_params)
frames = collect(at2, at2._N)
icr = at2._icr
neutral = at2._neutral_xy
# reconstruct body-frame foot xy = neutral + offset
body_xy = frames[:, :, :2] - np.asarray(p0)[None, :, :2] + neutral[None, :, :]
rad = np.hypot(body_xy[:, :, 0] - icr[0], body_xy[:, :, 1] - icr[1])
print("\nArcTurn radius-from-ICR per leg  min/max (constant => clean arc):")
for i in range(4):
    print(f"  leg {i}: {rad[:, i].min():.1f} .. {rad[:, i].max():.1f} mm")
print("\nOK")
