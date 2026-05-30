---
title: Foot positions are per-leg frame, not body frame
problem_type: design_pattern
module: motion/gaits, motion/stability, motion/kinematics
date: 2026-05-30
tags: [coordinate-frame, support-polygon, stability, kinematics, gaits]
---

# Foot positions are per-leg frame, not body frame

## The pitfall

Every gait `(4, 3)` position array, every `position_*` pose in `settings.py`, and the
`p0` a gait is built around are measured **from each leg's own femur pivot** — they
are *not* in a common body frame. `position_prowl` is `[0, 0, 113]` for all four
legs, but those feet are physically ~`robot_width` / ~`robot_length` apart.

> Two feet at the same per-leg coordinate are NOT at the same place.

This is invisible until you try to reason about the feet *relative to each other* —
a support polygon, a center-of-mass projection, a static-stability margin, any
whole-body geometry. Computed naively on the raw per-leg arrays, all four feet look
like they sit on top of each other and every such calculation is silently wrong.
Nothing in the kinematics pipeline composes the feet into a shared frame —
`validate_position` only checks single-leg reach; the coxa rotates each leg in its
own y–z plane (see `ROBOT.md`), and `coxa_length` is body-frame metadata not used in
the IK reach.

## The fix

Compose the feet into one body frame by adding each leg's **hip-mount corner offset**
before any cross-foot geometry. Corners (femur pivots), from the leg map
`0=FL, 1=FR, 2=BR, 3=BL` (body frame: X forward, Y right):

| Leg | Corner |
|---|---|
| 0 FL | `(+length/2, −width/2)` |
| 1 FR | `(+length/2, +width/2)` |
| 2 BR | `(−length/2, +width/2)` |
| 3 BL | `(−length/2, −width/2)` |

(The corner sign pattern matches `apply_body_tilt`'s yaw `[1,1,-1,-1]` / pitch
`[1,-1,-1,1]` in `kinematics.py`.) `src/motion/stability.py` implements this:
`body_frame_feet(positions)` → body-frame XY; `support_margin(feet, stance, com)` →
signed COM-to-nearest-edge distance (positive = inside = stable). COM is the body
geometric center (origin) plus an optional calibrated static offset; the COM ground
projection suffices for slow quasi-static gaits (ZMP not needed).

## Why it matters / where it bit

The static-wave prowl rebuild (`docs/plans/2026-05-30-002-...`) needed a
support-polygon stability gate. The body-frame composition — not the polygon math —
was the load-bearing, easy-to-get-wrong piece, because nothing in the codebase did
it and the per-leg convention is unstated in the gait arrays themselves.

## Related

- `src/motion/stability.py`, `test/test_stability.py`
- `ROBOT.md` → "Body frame & support polygon"
- Lateral y-sign convention (unmirrored coxa) lives in the gait layer, never
  kinematics — same "conventions are invisible in the data" family of pitfalls.
