---
date: 2026-05-30
topic: gait-stability
focus: more stable + composable gaits; fix prowl; assess kinematics; adequate tests
mode: repo-grounded
---

# Ideation: Gait Stability, Kinematics Sufficiency, Prowl Fix & Tests

This started as open ideation on "more stable gaits" and converged on four concrete
goals. The grounding investigation produced a linchpin finding (the kinematics gates
the rest), which reorders the goals into a forced sequence.

## Goals (as stated by the user)
1. Determine whether gaits need overall refactoring for stability + composability.
2. Determine whether the kinematics is sufficient (prior LLM edits made it worse).
3. Fix the prowl gait.
4. Ensure adequate tests (acknowledging real *dynamic* walking is hard to test).

## Grounding Context (codebase)
- Python quadruped. Robot(50Hz) → Controller(10Hz, gait exec) → QuadrupedKinematics; IMU(5Hz).
- Gait = iterator; `next(gait)` returns (4,3) mm offset array added to base pose `p0 + offset`.
- Two gait systems: manual `build_steps()` (gait.py/trot.py/prowl.py) and declarative
  `SimplifiedGait` (simplified_gait.py) — but the production trot (`SimpleTrotWithLateral`)
  bypasses `SimplifiedGait` and re-inherits `Gait`, so it's really 1.5 systems.
- Diagonal trot coordination baked into base class `get_offsets` (legs 0&2 welded, 1&3 welded).
- Configured gaits: trot/trot_reverse/trot_in_place/sidestep/turn/prowl/prowl_reverse active;
  `walk` has params but no impl; `crawl` is documented in GAITS.md:159 but has NO code.
- Stability today is thin: IMU broadcast but unused in gait loop; one-time auto-level only;
  no support-polygon/COM/static-margin checks anywhere; no duty-factor abstraction.
- Kinematics IK/FK marked "ORIGINAL ... PRESERVED" / "do not modify" — scar tissue from prior edits.

## Topic Axes
1. Static stability & support polygon
2. Foot trajectory shaping
3. Gait scheduling & phasing
4. Closed-loop stabilization (IMU feedback)
5. Gait architecture, authoring & tooling

---

## Assessment per goal

### Goal 2 — Kinematics sufficiency (the linchpin) — VERIFIED
**Verdict: the coxa convention is correct & intentional; there is exactly ONE real IK defect
(z vs √(y²+z²)), plus an incomplete FK. Trot-safe to fix.**

**Coxa topology (reverse-engineered + numerically verified).** Coxa axis points forward (+x)
and rotates the leg in the y–z plane; femur/tibia 2-link swings in the (x, radial) plane.
- `q3 = atan2(y, z)` is the geometrically correct coxa rotation, uniform across all legs.
- `angle_flip` coxa column = `[-1,-1,-1,-1]` (uniform) vs femur/tibia `[+1,-1,-1,+1]` (mirrored).
  The uniform coxa flip is the tell: **all four coxa servos are mounted the same way (NOT mirrored
  left/right).** This is intentional — confirmed by the user.
- Left/right "which way is outward" is therefore NOT in the kinematics; it is pushed into `y`-sign:
  gaits do `steps2_y = -steps1_y` (prowl.py:56, simplified_gait.py:178) + static stance offsets
  `[[10,0,0],[10,0,0],[0,-10,16],[0,10,16]]`. That is the "weirdness" — deliberate compensation.
- Servo pipeline (controller.py:67-68): `servo = (ik_angle − angle_zero) × angle_flip × scale + 500`.

**Numeric probe** (f=102,t=114,c=53; z positive ≈151 at stance):

| Foot pos (x,y,z) | curIK→code FK | curIK→TRUE FK (real error) | fixedIK→TRUE FK |
|---|---|---|---|
| `[100,0,151]`  | 0.00 | **0.00** | 0.000 |
| `[100,40,151]` | 40.00 | **5.21** | 0.000 |
| `[100,-60,151]`| 60.00 | **11.48** | 0.000 |
| `[80,90,120]`  | 90.00 | **30.00** | 0.000 |
| `[0,30,151]`   | 30.00 | **2.95** | 0.000 |

**Corrections to the first-pass diagnosis:**
- `coxa_length` being unused is **NOT a bug** — fixed IK round-trips to 0 without it, proving foot
  coords are measured from the femur pivot. Coxa length is body-frame metadata only.
- Column 1 (==|y|) was an FK *reporting* artifact, not foot misplacement. The real positioning
  error is the middle column.

**The one real IK defect:** the 2-link solve uses `z` where it must use the true in-plane radial
`√(y²+z²)` — both the `cos_q2` numerator and the `q1` `atan2` (kinematics.py:62 and :98). Effect:
0 error at y=0 (trot, hip_sway≈4mm → <0.1mm — that's why trot is stable), growing to ~30mm at
large lateral offset (sidestep / prowl / body-shift). Fix round-trips to 0.000mm and is identical
to current code at y=0, so **trot is untouched**. Likely what a prior edit thrashed: chasing
lateral behavior via coxa signs (not realizing coxa is deliberately unmirrored) and breaking trot.

**FK is separately incomplete:** returns `[-x, 0, z]` (kinematics.py:123), dropping the coxa
rotation, so FK is not the inverse of IK and cannot reconstruct lateral foot position. Needs a
true 3-DOF FK (validated: `foot=[-xin, rad·sin(q3), rad·cos(q3)]`).

**Safe fix path:** (a) IK: `radial = hypot(y,z)` in both solve paths; (b) FK: true 3-DOF with coxa
rotation. Guard both with IK→FK round-trip tests at y≠0 (currently `test_kinematics.py` only checks
y≈0, so the gap is never exercised). Low-risk: identical to current behavior at y=0.

### Goal 1 — Refactor for stability + composability? YES (hard architectural ceiling)
- Base class can only express 2 independent leg groups: `gait.py:116` returns
  `[steps1, steps2, steps1, steps2]` unless the unused `steps3`/`steps4` path is populated.
  **A one-leg-at-a-time gait is inexpressible in the default path** — this is the ceiling
  blocking a real prowl/crawl.
- The declarative `SimplifiedGait` exists but the production trot bypasses it (drift, not abstraction).
- No duty-factor / phase-offset model; phasing is implicit `np.roll`.
- Highest-value change: enable true 4-independent-leg movement + a phase/duty-factor model.

### Goal 3 — Fix prowl (two layers; real fix depends on 1 & 2)
Prowl is a slowed-down trot in a stalking costume: same diagonal-pair coupling (prowl.py:55-57
mirrors trot.py:24), lifts two opposite-corner feet at once → balances on a 2-point *line* with
no momentum to save it. Cosmetic tweaks (lower clearance, hip sway, lift-curve shape) can't make
a slow 2-feet-down gait stable. Real fix: one-leg-at-a-time wave gait with a body-shift sub-phase
(shift COM into the 3-foot support triangle before lifting), needing the per-leg path (Goal 1)
and benefiting from corrected kinematics (Goal 2). Also note a concrete impl smell: the stride
return vs lift-window timing leaves a horizontal foot reset at the cycle boundary.

### Goal 4 — Adequate tests (very achievable offline, no sim needed)
Dynamic balance is hard to test, but most failure modes are geometric/kinematic invariants that
need no robot — and none are currently checked (pytest isn't even installed; 2 trivial tests):
- IK↔FK round-trip at y≠0 (catches Goal 2).
- Foot-position continuity — no large jumps between consecutive steps (catches prowl's reset teleport).
- Reachability — `validate_position` across the full gait cycle for every leg.
- Static-stability-margin ≥ threshold per step (once a support-polygon primitive exists).

---

## Recommended Sequence (dependencies make order nearly forced)

### 1. Fix + test the kinematics — Axis: foundation (Goal 2 + start of 4)
**Description:** Two narrow changes: (a) IK uses `radial = hypot(y,z)` instead of `z` in both the
`cos_q2` numerator and the `q1` atan2 (kinematics.py:62,98); (b) FK becomes true 3-DOF with coxa
rotation (`foot=[-xin, rad·sin(q3), rad·cos(q3)]`, kinematics.py:123). Guard with IK→FK round-trip
tests at y≠0. Verified: round-trips to 0.000mm and is identical to current code at y=0 (trot-safe).
Do NOT touch the coxa convention (uniform unmirrored — intentional) or add coxa_length to the reach.
**Basis:** `direct:` numeric probe (true-FK error 5–30mm for y≠0, 0 at y=0). **Complexity:** Low–Medium.
**Confidence:** 92%. **Status:** Unexplored.

### 2. Offline test harness over existing gaits — Axis 5 (Goal 4)
**Description:** Install pytest; add continuity / reachability / round-trip invariants over the
*current* gaits to lock in behavior before refactoring; seed docs/solutions. **Basis:** `direct:`
2 trivial tests, no pytest. **Complexity:** Medium. **Confidence:** 85%. **Status:** Unexplored.

### 3. Refactor the gait core — Axis 3/5 (Goal 1)
**Description:** Enable 4-independent-leg movement (use/extend steps3/steps4) + an explicit
phase-offset + duty-factor model; converge the 1.5 systems onto one declarative foot-space spec.
**Basis:** `direct:` get_offsets 2-group ceiling; `external:` Spot Micro / Pupper foot-space
convergence + CPG phase model. **Complexity:** High. **Confidence:** 70%. **Status:** Unexplored.

### 4. Rebuild prowl as a static wave gait + support-polygon check — Axis 1 (Goal 3 + stability)
**Description:** One-leg-at-a-time sequence (e.g. 1→3→0→2) with a body-shift sub-phase moving COM
into the stance triangle incenter before each lift; add a `support_polygon` primitive (COM
projection, static-margin gate). **Basis:** `external:` McGhee&Frank β≥0.75, shift-then-swing;
`direct:` prowl=trot coupling. **Complexity:** High. **Confidence:** 80%. **Status:** Unexplored.

### Deferred / lower-priority survivors (from initial ideation)
- **Bezier / compound-cycloid swing trajectory** (zero-velocity touchdown, rearward retraction) —
  Axis 2. Reduces impact disturbance on all gaits. Fold in during step 3/4. Conf 82%.
- **Live IMU attitude correction in stance loop** — Axis 4. Highest-leverage closed-loop win on
  existing hardware, but layer it *after* static stability + corrected kinematics. Conf 80%.
- **CPG interpolated gait transitions** — Axis 3. Smooth trot↔prowl switching; natural extension
  of the step-3 phase model. Conf 70%.

## Rejection Summary
| # | Idea | Reason |
|---|------|--------|
| 1 | Shove-survival capture-step reflex | Reasoned-only, author-flagged as extrapolated; dynamic balance is a large leap depending on static primitives — revisit as a later brainstorm. |
| 2 | Duty-factor as standalone idea | Folded into the gait-core refactor (step 3) — it's a scheduler parameter. |
| 3 | Rearward foot retraction as standalone | Folded into the Bezier trajectory survivor. |
| 4 | Treat crawl as the broken gait | Corrected by user: crawl has no code; prowl is the broken/active one. Re-aimed the fix at prowl. |

Axis coverage across recommended + deferred: 1(#4), 2(Bezier), 3(#3,CPG), 4(IMU), 5(#2,#3). All covered.
