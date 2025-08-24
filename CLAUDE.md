# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Vega is a quadruped robot control system built in Python using a modular architecture with real-time control capabilities. The system consists of motion control (kinematics, gaits), sensor integration (IMU, camera), and a web-based control interface.

## Architecture

### Core Components

- **Motion System**: Inverse/forward kinematics for 4-legged robot with servo control
- **Gait Engine**: Abstract gait system supporting trot, sidestep, turn, jump gaits
- **Sensor Integration**: IMU (BNO055) for orientation, PiCamera2 for vision
- **Control Interface**: NiceGUI-based web interface for robot control
- **Node System**: Async node-based architecture using traitlets for communication

### Key Modules

- `src/motion/kinematics.py` - Core inverse/forward kinematics (QuadrupedKinematics class)
- `src/motion/gaits/` - Gait implementations extending abstract Gait class
- `src/nodes/robot.py` - Main Robot class orchestrating all components
- `src/nodes/controller.py` - Servo control and motion execution
- `src/nodes/imu.py` - IMU sensor integration
- `settings.py` - Configuration loading from settings.yml
- `app.py` - NiceGUI web interface

### Configuration

Robot configuration is managed through:
- `settings.yml` - Main configuration (dimensions, servo mappings, gait parameters)
- `settings.py` - Configuration loader with Settings class

## Development Commands

### Testing
```bash
# Run all tests
python3 -m pytest test/

# Run specific test file
python3 -m pytest test/test_kinematics.py

# Run with verbose output
python3 -m pytest -v test/
```

### Running the Robot

```bash
# Web interface (main control application)
python3 app.py

# Direct gait execution
python3 go.py

# IMU calibration
python3 calibrate_imu.py
```

### Development Tools

```bash
# Deploy changes (commits and pushes)
./deploy.sh

# Monitor system (if available)
./monitor.sh
```

## Important Implementation Details

### Kinematics System
- Uses standard DH parameters for 3-DOF legs (coxa, femur, tibia)
- X-coordinate inversion for world coordinate positioning
- Joint angles: [coxa_angle, femur_angle, tibia_angle]
- **CRITICAL**: Do not modify the math in kinematics.py without extensive testing

### Gait System
- All gaits inherit from abstract `Gait` class
- Step generation uses sinusoidal functions for smooth motion
- Gait parameters configurable in settings.yml
- Two-phase alternating leg movement (legs 0,2 vs legs 1,3)

### Settings Management
- Configuration loaded from settings.yml into Settings singleton
- Position offsets adjustable at runtime for leveling
- Environment variables can override config values (VEGA_ENVIRONMENT, etc.)

### Hardware Integration
- Servo communication via serial port (/dev/serial0)
- IMU calibration offsets stored in settings.yml
- Camera calibration matrix for vision processing
- Mock implementations available for development without hardware

## Code Conventions

- Use numpy arrays for positions/angles (shape: (4,3) for 4 legs, 3 joints)
- Positions in millimeters, angles in radians (unless specified as degrees)
- Leg numbering: 0=front-left, 1=front-right, 2=back-left, 3=back-right
- Error handling with logging via self.logger
- Async/await for non-blocking operations in nodes