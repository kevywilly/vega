# Ideation: A Better Turn Gait

- **Date:** 2026-05-30
- **Focus:** "Make a better turn gait — the current one works but is sloppy; maybe a new version."
- **Mode:** Repo-grounded (subject = `src/motion/gaits/turn.py`)
- **Status:** Ideation complete — survivors below, ready for brainstorm/plan on the chosen one.

---

## Grounding Context

**How gaits run.** Gaits are iterators emitting `(4,3)` foot-position arrays (mm). `Controller.spinner()`
calls `next(gait)` at `control_hz=50` and writes each frame **straight to vectorized IK** — there is
**no Cartesian interpolation layer** between frames. Servos move ~linearly in joint space between
consecutive frames. (`src/nodes/controller.py`)

**Current turn gait.** (`src/motion/gaits/turn.py`) *Corrected after grounding — the gait does **not**
actually rotate.* It is a `GaitSpec` 5-segment, one-leg-at-a-time gait: each leg lifts and steps in a
straight **lateral (y) line** in its own segment (legs 2,3 negated), then all four feet return laterally
together in a shared final segment. There is no x-component and no rotation about body Z anywhere — the
"turn" is a crab-shuffle whose net yaw is an emergent side effect. Lift already uses a smooth
`T.updown(fast=False)` arch. Params: `stride=35`, `clearance=50`, `step_size=15` → `num=6`, period 30.
`pivot_ratio=0.7` exists in `GaitParams` and is read by the base class but **no gait uses it**.

**The documented problem (constraint).**
- `GAITS.md`: *"Turn gait is sloppy — feet scrub the ground mid-rotation because stance feet follow a
  straight chord between start and end angle instead of the arc. This causes the body to wobble and the
  rotation to be inconsistent."*
- `settings.yml`: `# NOTE: stance feet chord across arc - causes scrub. needs fix.`

**Mechanism analysis (what actually makes it sloppy).**
1. **Feet translate, they don't rotate.** Each foot moves on a straight lateral line at radius `r` from
   the body centre — but the body it's supposed to turn rotates through an *arc*. Line-vs-arc is the
   literal definition of scrub. Verified: legacy `Turn` has `x travel = [0,0,0,0]` per leg.
2. **Shared planted lateral return.** The 5th segment drags all four *loaded* feet back to neutral on a
   straight line at once — the single largest scrub-and-wobble event per cycle.
3. **No world-frame planting.** A correct in-place turn requires each stance foot to rotate by exactly
   `-Δyaw` about the rotation centre so it stays fixed on the ground; the lateral shuffle can't.
4. **Open loop.** The BNO055 IMU publishes yaw on `Topics.raw_imu` but the turn gait ignores it, so net
   rotation per cycle is uncalibrated and inconsistent.

**Reuse available.** `simplified_gait.py` has an unused `_bezier()` quadratic-Bézier helper — a ready-made
swing-arc primitive.

**Topic axes:** (1) stance-path · (2) swing-trajectory · (3) phase-timing · (4) rotation-kinematics ·
(5) tuning-validation.

---

## Survivors (ranked)

### 1. Smooth swing-lift arc (mirror trot's sin profile) — *quick win*
- **Axis:** swing-trajectory
- **What:** Replace the constant `lift=clearance` for swing legs with `lift = clearance*sin(pi*t)` (or the
  existing `_bezier` helper) so the foot leaves and meets the ground at zero vertical velocity.
- **Basis:** `direct:` `turn.py` uses `lift=self.clearance` (constant); `trot.py` uses
  `z = self.clearance*np.sin(np.pi*t)` and is described as smooth. The fix is to port the proven pattern.
- **Why it matters:** This alone removes the foot "plop" at every step — likely the most visible chunk of
  the sloppiness, for a few lines of code.
- **Effort:** XS.

### 2. World-frame stance planting — *core correctness fix*
- **Axis:** stance-path
- **What:** Drive the gait off a continuous accumulated yaw `θ`. Place stance feet at `R(-θ)·p_neutral`
  every tick so each planted foot tracks the body's rotation and stays fixed on the ground (true arc,
  not chord). Set swing-foot touchdown so its horizontal velocity matches ground velocity at contact.
- **Basis:** `direct:` `GAITS.md`/`settings.yml` name the chord-vs-arc scrub as the root cause.
  `reasoned:` for in-place rotation, a foot is stationary in the world iff it rotates by `-Δyaw` in the
  body frame — a geometric identity, not a tuning knob.
- **Why it matters:** Directly eliminates scrub and the resulting wobble — the headline complaint.
- **Effort:** M.

### 3. Continuous phase-clock generation (on-demand, `step_size`-free)
- **Axis:** phase-timing / architecture
- **What:** Make `__next__` evaluate foot positions from a continuously advancing phase `φ` (and yaw `θ`)
  instead of replaying a precomputed 36-frame list. `step_size` becomes irrelevant; turn rate becomes a
  live parameter; phase-boundary jumps disappear because positions are a continuous function of `φ`.
- **Basis:** `direct:` base `Gait` precomputes `self._steps` and cycles them; the discreteness is what
  chords the arc at 50 Hz. `reasoned:` a continuous generator removes sampling artifacts at the source
  and is the natural carrier for #1 and #2.
- **Why it matters:** Fixes the discontinuity wobble *and* unlocks variable-speed turning; the same
  pattern lifts every other gait. Leverage.
- **Effort:** M.

### 4. ICR-parameterized unified motion `(vx, vy, ω)` — *the "new version"*
- **Axis:** rotation-kinematics
- **What:** Model all planar motion as velocity about an instantaneous center of rotation. In-place turn =
  `vx=vy=0, ω≠0`; arc-turn = offset ICR; turn-while-walking = `vx≠0, ω≠0`. Stance feet follow
  `ṗ = -(v + ω×r)`; the correct arc falls out automatically.
- **Basis:** `external:` ICR / differential-skid steering is the standard parameterization for
  ground-vehicle and quadruped planar locomotion (e.g. Spot/ANYmal-class controllers).
  `reasoned:` it subsumes #2 as a special case and makes "turn" stop being a bespoke gait.
- **Why it matters:** Replaces a one-off turn gait with a general locomotion model — biggest long-term
  leverage, and enables smooth arcing turns the robot can't do today.
- **Effort:** L. (Recommended as the strategic target; #1+#2 are the incremental path toward it.)

### 5. Wave/creep turn mode for wobble-free precise turning
- **Axis:** phase-timing
- **What:** Offer a second turn mode that moves **one** foot at a time (three always planted = statically
  stable) instead of diagonal pairs (two down = marginally stable, wobbles). Slower, but rock-steady for
  precise heading changes.
- **Basis:** `reasoned:` diagonal-pair turning keeps only 2 feet down; the support polygon collapses to a
  line through the body center, so any yaw torque imbalance tips/wobbles. A wave sequence keeps a true
  triangle of support throughout. `direct:` `walk.py` already moves one foot at a time — proven here.
- **Why it matters:** Attacks wobble structurally rather than by trajectory tuning; good "precision turn"
  companion to a fast diagonal turn.
- **Effort:** M.

### 6. Scrub metric + stance-displacement visualization / regression test
- **Axis:** tuning-validation
- **What:** Extend the per-gait visualization (`python3 src/motion/gaits/trot.py` pattern) to plot each
  stance foot's **world-frame** displacement during a turn and report total slip (mm). Turn it into a
  test asserting slip < threshold.
- **Basis:** `direct:` gaits already ship runnable visualizations; `reasoned:` "sloppy" is unmeasured
  today, so improvements can't be confirmed or protected from regression.
- **Why it matters:** Makes the fix verifiable and keeps it fixed. Pairs with every idea above.
- **Effort:** S.

### 7. Closed-loop IMU yaw correction *(honorable / second-order)*
- **Axis:** rotation-kinematics
- **What:** Read BNO055 yaw and trim `ω`/stride to hit a target heading and cancel drift.
- **Basis:** `direct:` IMU publishes on `Topics.raw_imu` but the turn gait is open-loop.
  `reasoned:` fixes the "inconsistent rotation" half of the complaint (magnitude accuracy), distinct from
  scrub (path accuracy).
- **Why it matters:** Turns "spin roughly" into "turn to exactly N degrees."
- **Effort:** M. Lower priority — do after the geometry is right (scrub first, then accuracy).

---

## Rejected (with reasons)

- **Increase `step_size` to make the chords finer.** Band-aid: treats the symptom (chord length) not the
  causes (constant lift, open-loop path, phase discontinuity); does nothing for the swing plop or wobble.
- **Bézier swing path as a separate idea.** Folded into #1 — it's an implementation option for the smooth
  lift (and the reuse note: `_bezier` already exists in `simplified_gait.py`).
- **Phase-boundary re-centering as a standalone fix.** Folded into #3 — continuity is automatic once
  positions are a continuous function of phase.
- **Touchdown velocity matching as a standalone fix.** Folded into #2 — it falls out of the correct arc.
- **Tank/skid-steer and CNC G02/G03 arc-interpolation framings.** These are the *basis/rationale* for #2
  and #4, not separate deliverables.
- **Subject-replacement (add wheels, use a turntable base, switch robots).** Out of scope — the ask is a
  better *turn gait* for this quadruped.

*Axis coverage: all 5 axes have at least one survivor.*

---

## Recommended path

- **Minimal "better turn gait":** #1 (smooth lift) + #2 (world-frame stance arc), verified by #6.
  Small, high-confidence, kills most of the sloppiness.
- **The "new version" you hinted at:** #3 (continuous phase clock) carrying #1+#2, then #4 (ICR model) as
  the general successor — with #5 as a selectable precision mode and #7 for heading accuracy.

## Built (2026-05-30) — experiment

Per "play time, let's try both," two new gait classes were built (legacy `Turn` left untouched; its
migration tests pin it byte-for-byte):

- **`src/motion/gaits/simple_turn.py` — `SimpleTurn`** (survivors #1 + #2). Trot structure (diagonal
  pairs, smooth sin lift) but each foot offset is `R_z(angle)·r_i − r_i` — a genuine rotation about the
  body centre instead of a lateral line. Stays a precomputed `GaitSpec` gait.
- **`src/motion/gaits/arc_turn.py` — `ArcTurn`** (survivors #3 + #4). Continuous float-phase generator
  (overrides `__next__`), ICR-parameterised (`pivot_ratio` shifts the centre fore/aft → spin vs arc
  turn), world-frame stance planting (planted feet rotate rigidly about the ICR by `-dψ`/tick → scrub-free
  by construction), smoothstep swing reposition + sin lift. Exposes `degrees_per_cycle()`.

**Verification** (`verify_turns.py`, repo root):

| | x-travel/leg | feet trace arcs | scrub signature |
|---|---|---|---|
| legacy `Turn` | `[0,0,0,0]` (pure-Y chord) | ❌ | — |
| `SimpleTurn` | `[36,36,36,36]` | ✅ | — |
| `ArcTurn` | `[33,30,40,32]` | ✅ | radius-from-ICR constant ±2 mm/cycle |

Not yet wired into `controller.py` `MoveTypes` (still bench experiments). Geometry uses a documented
corner convention; net-yaw *sign/magnitude* and hardware feel still want a real-robot pass.

## Next step

Pick one survivor (or the recommended bundle) and run **`ce-brainstorm`** to define it precisely, or
**`ce-plan`** to go straight to an implementation plan.
