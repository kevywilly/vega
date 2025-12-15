# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Vega is a quadruped robot control system built in Python. The system runs on Jetson/Pi hardware with servo-based leg control, IMU stabilization, and a web-based interface.

## Architecture

### Node System
The robot uses an async node-based architecture (`src/nodes/node.py`). Each node inherits from `Node` and implements a `spinner()` method called at a configurable frequency. Nodes communicate via blinker signals defined in `src/signals.py`:
- `Topics.raw_imu` - IMU sensor data
- `Topics.raw_pose` - Robot pose updates
- `Topics.raw_image` - Camera frames

### Control Flow
```
app.py (NiceGUI web UI)
    └── Robot (orchestrator)
            ├── Controller (servo control, gait execution)
            │       └── QuadrupedKinematics (IK/FK math)
            └── IMU (orientation sensing)
```

### Gait System
Two gait implementations exist (see `GAITS.md` for details):
1. **Current system** (`src/motion/gaits/gait.py`): Manual numpy array construction with `build_steps()`
2. **Simplified system** (`src/motion/gaits/simplified_gait.py`): Declarative pattern-based approach with `define_leg_movements()`

Gaits are iterators - call `next(gait)` to get the next position array.

## Development Commands

```bash
# Run all tests
python3 -m pytest test/

# Run specific test file
python3 -m pytest test/test_kinematics.py -v

# Web interface (main application)
python3 app.py

# Test individual gaits (includes visualization)
python3 src/motion/gaits/trot.py

# Deploy changes
./deploy.sh
```

## Configuration

`settings.yml` contains all robot configuration. Key sections:
- `servos`: 4x3 array of servo IDs per leg/joint
- `dimensions`: leg segment lengths (coxa, femur, tibia in mm)
- `positioning`: angle_flip, angle_zero calibration, offsets
- `gait_params`: stride, clearance, step_size per gait type

Environment variables: `VEGA_ENVIRONMENT`, `VEGA_CONFIG_FILE`, `SERIAL_PORT`

## Critical Implementation Details

### Kinematics (`src/motion/kinematics.py`)
- **CRITICAL**: Do not modify IK/FK math without extensive testing
- X-coordinate is inverted for world coordinate positioning
- Joint order: [coxa, femur, tibia]
- Vectorized IK available: `inverse_kinematics_vectorized()` for 4x speedup

### Leg Layout
```
L0---L1    (0=front-left, 1=front-right)
   *
L3---L2    (2=back-right, 3=back-left)
```
Diagonal pairs move together in trot: (0,3) and (1,2)

### Hardware
- Serial port: `/dev/ttyTHS1` (Jetson) or `/dev/serial0` (Pi)
- IMU: BNO055 via I2C with calibration offsets in settings
- Mock implementations in `src/mock/` for development without hardware

## Code Conventions

- Positions: numpy arrays shape (4,3), units in millimeters
- Angles: radians internally, degrees in settings.yml
- All nodes use `self.logger` for logging
- Runtime offset adjustments via `settings.position_offsets` (not cached)