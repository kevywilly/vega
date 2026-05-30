# ROBOT.md — Vega Quadruped

Hardware and capability reference for the Vega quadruped robot. This document
describes the *physical machine* and what it can do. For software architecture
conventions see `CLAUDE.md`; for gait internals see `GAITS.md`.

All values below are sourced from `settings.yml` and the codebase. Where a fact
is inferred rather than stated explicitly, it is marked _(inferred)_.

---

## 1. At a Glance

| Property | Value |
|---|---|
| Type | 12-DOF quadruped (4 legs × 3 joints) |
| Compute | NVIDIA Jetson (JetPack / `nvidia-container-runtime`) _(inferred from docker config)_ |
| Actuators | 12× LewanSoul/Hiwonder **LX-16A** serial bus servos |
| Servo bus | Single half-duplex serial line, `/dev/ttyTHS1` (Jetson) / `/dev/serial0` (Pi) |
| IMU | Bosch **BNO055** 9-DOF (I²C), NDOF fusion mode |
| Camera | CSI camera, default `1640×1232 @ 29fps` |
| Body | 223 mm long × 142 mm wide |
| Leg reach | 12 mm (min) to 216 mm (max), per leg |
| Control loop | Robot 50 Hz · Controller 10 Hz · IMU 5 Hz |
| Interface | NiceGUI web app (`app.py`), optional WebRTC video + YOLO nav |

---

## 2. Mechanical Layout

### Leg numbering

```
 L0 -------- L1      0 = Front-Left
    \      /         1 = Front-Right
     \    /          2 = Rear-Right
     /    \          3 = Rear-Left
    /      \
 L3 -------- L2
```

Legs are numbered clockwise from the front-left. Diagonal pairs `(0, 2)` and
`(1, 3)` move together in the trot and prowl gaits.

### Dimensions (`settings.yml › dimensions`, millimeters)

| Segment | Length (mm) | Role |
|---|---|---|
| Coxa | 53 | Hip — rotates the leg laterally (in/out) |
| Femur | 102 | Upper leg — primary lift/reach |
| Tibia | 114 | Lower leg — foot/contact link |
| Body width | 142 | Lateral spacing between left/right legs |
| Body length | 223 | Longitudinal spacing front-to-rear |

**Per-leg reach envelope** (2D, in the femur/tibia plane):
- Max reach = femur + tibia = **216 mm** (leg fully extended)
- Min reach = |femur − tibia| = **12 mm** (leg fully folded)

Positions outside `[12, 216]` mm are unreachable; `QuadrupedKinematics.validate_position()`
checks this, and the IK clamps `cos(q2)` to `[-1, 1]` so out-of-range targets
degrade gracefully instead of producing `NaN`.

---

## 3. Servos & Actuation

### Hardware

- **12 servos total**, 3 per leg, joint order **[coxa, femur, tibia]**.
- Model: LewanSoul/Hiwonder **LX-16A** serial bus servos (logger
  `lewansoul.servos.lx16a`, LewanSoul command set in `src/motion/servo_controller.py`).
- All servos share one half-duplex serial bus addressed by ID.
- Position range **0–1000** over a **240°** mechanical span; center = 500.

### Servo ID map (`settings.yml › servos`)

```
servos: [[11,12,13], [21,22,23], [31,32,33], [41,42,43]]
```

| Leg | Coxa ID | Femur ID | Tibia ID |
|---|---|---|---|
| 0 — Front-Left | 11 | 12 | 13 |
| 1 — Front-Right | 21 | 22 | 23 |
| 2 — Rear-Right | 31 | 32 | 33 |
| 3 — Rear-Left | 41 | 42 | 43 |

The tens digit encodes the leg (1–4), the ones digit the joint (1=coxa, 2=femur, 3=tibia).

### Serial protocol (`src/motion/servo_controller.py`)

LewanSoul command set. Commands in use:

| Command | Code | Purpose |
|---|---|---|
| `CMD_SERVO_MOVE` | 3 | Move servo(s) to position over a time window (0–30000 ms) |
| `CMD_ACTION_GROUP_RUN` | 6 | Run a stored action group |
| `CMD_ACTION_STOP` | 7 | Stop action group |
| `CMD_ACTION_SPEED` | 11 | Set action speed |
| `CMD_GET_BATTERY_VOLTAGE` | 15 | Read pack voltage |
| `CMD_MULT_SERVO_UNLOAD` | 20 | Release torque on multiple servos |
| `CMD_MULT_SERVO_POS_READ` | 21 | Read positions of multiple servos |

Concurrency design: write commands (move, unload) are **lock-free** for throughput;
read/query commands serialize through an `asyncio.Lock` so responses don't interleave.

### Angle → servo position math (`src/nodes/controller.py`)

```python
SERVO_MAX_ANGLE = radians(240)          # full mechanical span
_SERVO_SCALE    = 1000.0 / SERVO_MAX_ANGLE   # ≈ 238.7 units per radian

servo_value = (angle - angle_zero) * angle_flip * _SERVO_SCALE + 500
```

- `angle` is the joint angle in **radians** from IK.
- Result is an integer position in the servo's `0–1000` range, centered at `500`.
- The inverse (`_angles_from_servo_positions`) recovers radians from a position read.

### Calibration (`settings.yml › positioning`)

| Field | Value | Meaning |
|---|---|---|
| `angle_zero` | `[[0,90,33], …]` (deg) | Neutral joint angles; subtracted before scaling |
| `angle_flip` | `[[-1,1,1], [-1,-1,-1], [-1,-1,-1], [-1,1,1]]` | Per-joint direction (±1) to correct mirrored mounting |
| `offsets` | `[[10,0,0],[10,0,0],[0,-10,16],[0,10,16]]` | Per-leg XYZ position trim (mm), applied during IK |
| `ready_height_pct` | `0.70` | Standing height as a fraction of max reach |

The `angle_flip` pattern reflects the physical mirroring of legs: left and right
sides rotate in opposite directions for the same commanded motion.

---

## 4. Kinematics (`src/motion/kinematics.py`)

`QuadrupedKinematics` solves a 2-link planar arm (femur + tibia) per leg plus a
lateral coxa rotation. **The math is intentionally frozen — do not modify IK/FK
without extensive round-trip testing** (see `CLAUDE.md`).

- **Joint order:** `[coxa, femur, tibia]` → returned as `[q3, q1, q2]`.
- **Coordinate frame:** X is **inverted** (`x = -x`) for world positioning; Z is
  the vertical (lift) axis; Y drives the coxa's lateral angle.
- **IK** (`inverse_kinematics_vectorized`): law-of-cosines for the knee (`q2`),
  two-link geometry for the shoulder (`q1`), `atan2(y, z)` for the coxa (`q3`).
  Processes all 4 legs at once — **~4× faster** than the per-leg loop.
- **FK** (`forward_kinematics`): reconstructs `[x, y, z]` from joint angles.
- **Body tilt** (`apply_body_tilt`): applies pitch/yaw by offsetting each leg's Z:
  - positive **yaw** = nose up, scaled by `length/2 · sin(yaw)`
  - positive **pitch** = roll clockwise, scaled by `width/2 · sin(pitch)`
  - per-leg sign patterns: yaw `[1,1,-1,-1]`, pitch `[1,-1,-1,1]`

Positions throughout the system are numpy arrays of shape `(4, 3)` in
**millimeters**; angles are **radians** internally, **degrees** in `settings.yml`.

---

## 5. Gaits

Gaits are Python **iterators** — `next(gait)` returns the next `(4, 3)` position
array. Two implementations coexist (see `GAITS.md`): the manual `build_steps()`
system and the declarative `simplified_gait.py` pattern system.

### Parameters (`settings.yml › gait_params`)

| Gait | Stride (mm) | Clearance (mm) | Step size (°) | Hip sway (mm) |
|---|---|---|---|---|
| `trot` | 55 | 65 | 15 | 4 |
| `trot_reverse` | −30 | 40 | 12 | 6 |
| `trot_in_place` | 0 | 40 | 25 | 0 |
| `walk` | 50 | 60 | 12 | 6 |
| `sidestep` | 30 | 30 | 12 | — |
| `turn` | 35 | 50 | 15 | 6 |
| `prowl` | 40 | 35 | 15 | 8 |
| `prowl_reverse` | −30 | 30 | 15 | 8 |

- **stride** — horizontal travel per cycle (negative = reverse)
- **clearance** — foot lift height during swing
- **step_size** — degrees of phase advanced per step; `num_steps = 90 / step_size`
  sets the resolution/smoothness of each phase
- **hip_sway** — lateral weight-shift amplitude for balance

### Gait files (`src/motion/gaits/`)

- `trot.py` — diagonal-pair trot (forward / reverse / in-place)
- `prowl.py` — low, slow stalking gait with ~75% stance (ground-contact) phase
- `turn.py` — in-place / arc turning, per-leg phased
- `simplified_gait.py` — `SimpleTrotWithLateral`, `SimpleSidestep`, reusable
  `MovementPattern` primitives (lift, stride, sway, …)
- `gait.py` / `gait_params.py` — base class and `GaitParams` dataclass

---

## 6. Sensing

### IMU — Bosch BNO055 (`src/nodes/imu.py`)

- 9-DOF sensor over **I²C** (`board.I2C()`), running in **NDOF** fusion mode
  (full sensor fusion with on-chip orientation).
- Polled at **5 Hz**; broadcasts on `Topics.raw_imu`.
- `IMUData` exposes: `euler` `[heading, roll, pitch]` (deg), `acceleration`
  (m/s²), `gyro` (rad/s), plus convenience properties `heading`, `roll`,
  `pitch`, `angular_vel`, `angular_accel`.

Calibration offsets (`settings.yml › imu.offsets`):

```yaml
magnetic:     [-255, -185, 728]
gyro:         [1, 2, 1]
acceleration: [29, -10, -20]
```

### Camera (`settings.yml › sensors.camera`)

- CSI camera; default sensor mode `MODE1640x1232X29` (1640×1232 @ 29 fps).
- Intrinsic matrix `K` and 5-term distortion coefficients are stored for
  undistortion / vision work:

  ```
  K = [[848.72,   0.00, 939.51],
       [  0.00, 848.97, 596.15],
       [  0.00,   0.00,   1.00]]
  distortion = [-0.296850, 0.061372, 0.002562, -0.002645, 0.0]
  ```

- Optional pipeline: WebRTC video out (`:8554`) and YOLO obstacle detection
  feeding `Topics.obstacles` for autonomous navigation.

---

## 7. Software Architecture (summary)

Async node system (`src/nodes/node.py`): each node implements `spinner()`, called
at a fixed frequency by `spin()`. Nodes are decoupled via **blinker** signals
(`src/signals.py`): `raw_imu`, `raw_pose` (`'pose_raw'`), `raw_image`, `obstacles`.

```
app.py (NiceGUI web UI)
└── Robot (orchestrator, 50 Hz)
        ├── Controller (10 Hz) ── servo control, gait stepping, IK/FK
        │       ├── QuadrupedKinematics
        │       └── ServoController (LX-16A serial)
        ├── IMU (5 Hz) ── BNO055 orientation
        └── Navigator (optional) ── YOLO obstacle avoidance
```

Hardware-free development uses mocks in `src/mock/` (`adafruit_bno055`, `board`,
`picamera2`). If the serial port can't open, the `ServoController` is set to
`None` and the robot runs without moving — useful for desk testing.

---

## 8. Capabilities

### Movement commands (`MoveTypes`, `src/model/types.py`)

`FORWARD`, `FORWARD_LT`, `FORWARD_RT`, `BACKWARD`, `BACKWARD_LT`, `BACKWARD_RT`,
`LEFT`, `RIGHT`, `TROT_IN_PLACE`, `PROWL`, `PROWL_BACKWARD`, `STOP`.

These map to gait selections: directional trot, arc/turn variants, lateral
sidestep, in-place trotting, and the prowl gait (forward/back).

### Poses (`settings.py`)

Pre-defined stances at varying heights: `home` (max), `ready` (~70%), `trot`,
`walk`, `prowl`, `crouch`, `sit` (weight shifted rearward). The web UI exposes
buttons for these plus a demo sequence.

### Stabilization & leveling

- IMU-driven **auto-level** (`Robot.level()`): trots in place while reading roll,
  adjusts per-leg Z offsets (pattern `[1,-1,-1,1]`) until `|roll| < 0.5°`, up to
  ~10 iterations. Thresholds in `settings.yml › leveling`.
- **Body tilt** (pitch/yaw) applied geometrically via `apply_body_tilt`.
- Runtime trim via `settings.position_offsets` (intentionally *not* cached so
  leveling can adjust it live); `reset_offsets()` restores defaults.

### Web interface (`app.py`)

NiceGUI app (port 8080): directional movement grid, prowl + pose buttons,
auto-level / reset-offsets controls, optional navigation toggle, and live
telemetry — heading/roll/pitch, angular velocity & acceleration, and per-leg
positions, joint angles, and offsets.

---

## 9. Hardware Configuration & Environment

| Item | Setting |
|---|---|
| Serial port | `/dev/ttyTHS1` (Jetson) · `/dev/serial0` (Pi fallback) |
| Default move time | 800 ms (`DEFAULT_MILLIS`) |
| Robot node rate | 50 Hz |
| Controller node rate | 10 Hz |
| IMU node rate | 5 Hz |
| Web UI port | 8080 |
| WebRTC video port | 8554 |

**Environment variables:** `VEGA_ENVIRONMENT`, `VEGA_CONFIG_FILE` (override
`settings.yml` path), `SERIAL_PORT` (override serial device).

---

## 10. Quick Reference — Key Files

| Concern | File |
|---|---|
| All configuration | `settings.yml` |
| Config loader / poses | `settings.py` |
| IK / FK / body tilt | `src/motion/kinematics.py` |
| Servo serial driver | `src/motion/servo_controller.py` |
| Angle↔servo mapping, control | `src/nodes/controller.py` |
| IMU driver | `src/nodes/imu.py` |
| Gaits | `src/motion/gaits/` |
| Signals / topics | `src/signals.py` |
| Node base class | `src/nodes/node.py` |
| Web UI | `app.py` |
| Hardware mocks | `src/mock/` |
