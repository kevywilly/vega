# Gaits System Documentation

This document explains how to create, modify, and run gaits for the Vega quadruped robot.

## Table of Contents
- [Overview](#overview)
- [Running Gaits](#running-gaits)
- [Current Gait System](#current-gait-system)
- [Simplified Gait System](#simplified-gait-system)
- [Available Gaits](#available-gaits)
- [Creating New Gaits](#creating-new-gaits)
- [Migration Guide](#migration-guide)

## Overview

A gait defines the coordinated movement pattern of the robot's four legs. Each gait generates a sequence of foot positions that create locomotion (walking, trotting, jumping, etc.).

### Coordinate System
- **X-axis**: Forward/backward (positive = forward)
- **Y-axis**: Left/right lateral movement (positive = right)
- **Z-axis**: Up/down (positive = up from ground)
- **Leg numbering**: 0=front-left, 1=front-right, 2=back-right, 3=back-left

## Running Gaits

### Quick Testing
```bash
# Test individual gaits
python3 src/motion/gaits/trot.py
python3 src/motion/gaits/trot_with_lateral.py

# Test with robot (be careful!)
python3 test_lateral_trot.py
```

### Using in Robot Code
```python
from src.motion.gaits.trot import Trot
from src.nodes.robot import Robot

robot = Robot()
gait = Trot(
    p0=settings.position_ready,
    stride=50,        # Forward distance per step (mm)
    clearance=60,     # Lift height (mm)
    step_size=15      # Degrees per step (controls speed)
)

# Execute gait steps
for i in range(20):
    position = next(gait)
    robot.controller.move_to(position, 100)  # 100ms per step
```

### Via Web Interface
Gaits are integrated into the robot control system via `MoveTypes` in `app.py`:
- **FORWARD**: Uses trot gait with forward offsets
- **BACKWARD**: Uses reversed trot gait
- **LEFT/RIGHT**: Uses sidestep gait
- **FORWARD_LT/RT**: Uses turn gait

## Gait Core: GaitSpec (current system)

As of the gait-core refactor (`docs/plans/2026-05-30-001-refactor-gait-core-phasing-plan.md`),
gaits are defined **declaratively** with a `GaitSpec` and compiled into the canonical
per-leg step array. This supersedes the two older systems below (kept for reference;
only `prowl` still uses the legacy imperative path, pending its rebuild).

### The model

A gait is `(period, duty_factor, 4 × LegSpec)`:

- **period** `N` — ticks in one full cycle.
- **duty_factor** `β` — fraction of the cycle each foot is in stance (~0.75 for the
  current gaits; ≥0.75 for a statically stable wave gait).
- **LegSpec** per leg — a `phase_offset φ ∈ [0,1)` plus `x`/`y`/`z` trajectory
  callables (`N → (N,)` mm offsets; a `None` axis is zeros).

Timing (phase) is separate from trajectory shape, following the MIT Cheetah /
Stanford Pupper gait-scheduler model. Phase math lives in `phase.py`
(`local_phase`, `in_stance`, `swing_phase`, `phase_to_ticks`); trajectory shapes
live in `trajectories.py` — the **single source** of shape math (`stride_forward`,
`downupdown`, `lift`, `trot_lateral_pattern`, …).

### Authoring a gait

```python
import numpy as np
from src.motion.gaits.gait import Gait
from src.motion.gaits.gait_spec import GaitSpec, LegSpec, compile_spec
from src.motion.gaits import trajectories as T

class MyGait(Gait):
    def build_steps(self):
        self.steps = compile_spec(self._spec())

    def _spec(self):
        num = self.num_steps
        def z(_n):
            return np.hstack([T.downupdown(num), T.zero(num * 3)]) * (-self.clearance)
        a = LegSpec(z=z, phase_offset=0.0)    # legs 0, 2
        b = LegSpec(z=z, phase_offset=0.5)    # legs 1, 3 (diagonal half-cycle)
        return GaitSpec(period=num * 4, duty_factor=0.75, legs=[a, b, a, b])
```

`compile_spec` builds each leg's `(N,3)` base from its callables and realizes the
phase offset as an integer `np.roll` (`phase_to_ticks(φ, N)`). Set `self.steps`
directly; the base `Gait` iterator indexes it. For a one-leg-at-a-time **wave gait**,
give all four legs distinct phase offsets (e.g. `[0, .25, .5, .75]` with `β=0.75`) —
see `test/test_wave_gait_expressibility.py`.

### Lateral (y) sign convention

Left/right "outward" is the **sign of y in the gait**, not in the kinematics (the
coxa is deliberately unmirrored — see ROBOT.md). A diagonal pair's second leg
declares `-y` of the first; never push this into the kinematics layer.

### Status

- **trot / trot-in-place, sidestep, turn** — on GaitSpec.
- **prowl** — still imperative (`prowl.py`), the last legacy holdout; rebuilt as a
  static wave gait in a follow-up (plan item 4).
- The two sections below are **legacy**, retained for reference only.

---

## Current Gait System (legacy)

> **Legacy.** Superseded by GaitSpec above. Only `prowl` still builds this way.

### Structure
Legacy gaits inherit from the `Gait` base class and implement `build_steps()`,
building the step arrays imperatively:

```python
class MyGait(Gait):
    def build_steps(self):
        # Build movement arrays manually
        x = np.hstack([...])  # Forward/back movement
        y = np.hstack([...])  # Lateral movement  
        z = np.hstack([...])  # Up/down movement
        
        self.steps1 = Gait.reshape_steps(np.array([x, y, z]), total_steps)
        self.steps2 = np.roll(self.steps1, phase_shift, axis=0)
```

### Base Class Methods
The `Gait` class provides helper methods:
- `stride_forward()`: Sine wave for forward motion
- `stride_back()`: Cosine wave for return motion
- `updown()`: Sine wave for lift motion
- `downupdown()`: Modified lift with ground contact
- `zeros`: Array of zeros

### Current Implementations

**Trot** (`src/motion/gaits/trot.py`):
- Diagonal leg pairs (0,2) and (1,3)
- Phase offset of half-cycle between pairs
- Standard forward locomotion

**TrotWithLateral** (`src/motion/gaits/trot_with_lateral.py`):
- Same as trot but adds lateral hip movement
- Configurable lateral amplitude
- Opposite lateral movement for diagonal legs

**Sidestep** (`src/motion/gaits/sidestep.py`):
- Lateral movement instead of forward
- Diagonal leg coordination

**Turn** (`src/motion/gaits/turn.py`):
- Individual leg control for turning
- Complex 4-leg phase relationship

**Jump** (`src/motion/gaits/jump.py`):
- All legs move together
- Vertical movement only

## Simplified Gait System (legacy)

> **Legacy.** This `SimplifiedGait`/`LegMovement` system only ever read legs 0 and
> 1 and welded the rest, so it could not express a 4-independent-leg gait. It is
> superseded by GaitSpec and has no production users. Use GaitSpec instead.

An older declarative system in `src/motion/gaits/simplified_gait.py`.

### Key Benefits
- **Declarative**: Define what each leg should do, not how
- **Reusable patterns**: Pre-built movement functions
- **Clear coordination**: Explicit phase relationships
- **Less code**: ~10 lines vs ~50 lines per gait

### Movement Patterns
Pre-built patterns in `MovementPattern` class:
```python
MovementPattern.lift(steps, height)          # Up-down motion
MovementPattern.step_cycle(steps, distance)  # Forward-back cycle
MovementPattern.lateral_sway(steps, amplitude) # Side-to-side
MovementPattern.zero(steps)                  # No movement
```

### Creating Simplified Gaits
```python
class MySimpleGait(SimplifiedGait):
    def define_leg_movements(self) -> Dict[int, LegMovement]:
        def my_x_pattern(steps):
            return MovementPattern.step_cycle(steps, self.stride)
        
        def my_z_pattern(steps):
            return MovementPattern.lift(steps, self.clearance)
        
        half_cycle = self.num_steps * 2
        return {
            0: LegMovement(x=my_x_pattern, z=my_z_pattern, phase_shift=0),
            1: LegMovement(x=my_x_pattern, z=my_z_pattern, phase_shift=half_cycle),
            2: LegMovement(x=my_x_pattern, z=my_z_pattern, phase_shift=half_cycle),
            3: LegMovement(x=my_x_pattern, z=my_z_pattern, phase_shift=0),
        }
```

## Available Gaits

| Gait | File | Description | Parameters |
|------|------|-------------|------------|
| Trot | `trot.py` | Basic diagonal trot | stride, clearance, step_size |
| TrotWithLateral | `trot_with_lateral.py` | Trot + hip sway | + hip_sway |
| Sidestep | `sidestep.py` | Lateral movement | stride, clearance, step_size |
| Turn | `turn.py` | In-place turning | stride, clearance, turn_direction |
| Jump | `jump.py` | Vertical jumping | clearance, step_size |
| TigerRun | `tiger_run.py` | Aggressive running | stride, clearance, step_size |
| Crawl | `crawl.py` | Slow crawling | stride, clearance, step_size |

### Simplified Versions
| Gait | Class | Description |
|------|-------|-------------|
| SimpleTrot | `simplified_gait.py` | Clean trot implementation |
| SimpleTrotWithLateral | `simplified_gait.py` | Trot with lateral movement |
| SimpleJump | `simplified_gait.py` | All legs jumping together |
| SimpleSidestep | `simplified_gait.py` | Clean sidestep implementation |

## Creating New Gaits

### Method 1: Current System (Complex but Functional)

1. **Inherit from Gait**:
```python
from src.motion.gaits.gait import Gait

class MyGait(Gait):
    def build_steps(self):
        # Define your movement patterns
```

2. **Build movement arrays**:
```python
# Forward/backward movement
x = np.hstack([
    self.stride_forward() * self.stride,
    self.stride_back() * self.stride
])

# Lateral movement (usually zeros for forward gaits)
y = np.repeat(self.zeros, 2)

# Vertical movement
z = np.hstack([
    self.updown() * -self.clearance,
    self.zeros
])
```

3. **Create leg step sequences**:
```python
self.steps1 = Gait.reshape_steps(np.array([x, y, z]), total_steps)
self.steps2 = np.roll(self.steps1, phase_offset, axis=0)
```

### Method 2: Simplified System (Recommended)

1. **Inherit from SimplifiedGait**:
```python
from src.motion.gaits.simplified_gait import SimplifiedGait, LegMovement, MovementPattern

class MyGait(SimplifiedGait):
    def define_leg_movements(self):
        # Define movement for each leg
```

2. **Define movement functions**:
```python
def my_stride_pattern(steps):
    return MovementPattern.step_cycle(steps, self.stride)

def my_lift_pattern(steps):
    return MovementPattern.lift(steps, -self.clearance)
```

3. **Map legs to movements**:
```python
return {
    0: LegMovement(x=my_stride_pattern, z=my_lift_pattern),
    1: LegMovement(x=my_stride_pattern, z=my_lift_pattern, phase_shift=offset),
    # ... etc
}
```

## Common Gait Patterns

### Diagonal Coordination (Trot)
- Legs 0,3 move together (diagonal pair)
- Legs 1,2 move together (opposite diagonal)
- Phase shift of half-cycle between pairs

### Sequential Coordination (Walk)
- Each leg moves individually
- Phase shifts of quarter-cycle: 0, 25%, 50%, 75%

### Lateral Coordination (Pace)
- Left legs (1,2) move together
- Right legs (0,3) move together
- Half-cycle phase shift

### All Together (Jump)
- All legs identical movement
- No phase shifts

## Configuration

### Gait Parameters
Configure default gait parameters in `settings.yml`:
```yaml
gait_params:
  trot:
    stride: 55
    clearance: 65
    step_size: 15
  trot_reverse:
    stride: -30
    clearance: 40
    step_size: 12
```

### Robot Integration
Gaits are used in `src/nodes/robot.py` via `process_move()`:
```python
def process_move(self, move_type: MoveTypes):
    if move_type == MoveTypes.FORWARD:
        self.gait = Trot(**settings.trot_params)
    # ... etc
```

## Testing and Debugging

### Visualization
Most gaits support plotting:
```python
gait = MyGait(...)
gait.plotit()  # Shows matplotlib plots of leg movements
```

### Step-by-step Testing
```python
gait = MyGait(...)
for i in range(10):
    positions = next(gait)
    print(f"Step {i}: {positions}")
```

### Safety Testing
Always test new gaits:
1. **In simulation first** (with mock hardware)
2. **With small parameters** (low stride, clearance)
3. **Ready to emergency stop**
4. **Check for valid positions** (within robot reach limits)

## Migration Guide

To migrate from current to simplified system:

1. **Identify the movement pattern**:
   - What does each leg do in X, Y, Z?
   - What are the phase relationships?

2. **Convert to movement functions**:
   - Replace `np.hstack([...])` with `MovementPattern` calls
   - Extract reusable patterns

3. **Define leg movements**:
   - Map each leg number to a `LegMovement`
   - Specify phase shifts explicitly

4. **Test equivalence**:
   - Compare outputs of old vs new implementation
   - Verify same movement patterns

### Example Migration
```python
# OLD
def build_steps(self):
    x = np.hstack([self.stride_forward(), self.stride_back()]) * self.stride
    y = np.repeat(self.zeros, 2)
    z = np.hstack([self.updown(), self.zeros]) * -self.clearance
    self.steps1 = Gait.reshape_steps(np.array([x, y, z]), self.num_steps * 2)
    self.steps2 = np.roll(self.steps1, self.num_steps, axis=0)

# NEW
def define_leg_movements(self):
    def stride_pattern(steps):
        return MovementPattern.step_cycle(steps, self.stride)
    def lift_pattern(steps):
        return MovementPattern.lift(steps, -self.clearance)
    
    return {
        0: LegMovement(x=stride_pattern, z=lift_pattern),
        1: LegMovement(x=stride_pattern, z=lift_pattern, phase_shift=self.num_steps),
        2: LegMovement(x=stride_pattern, z=lift_pattern, phase_shift=self.num_steps),
        3: LegMovement(x=stride_pattern, z=lift_pattern),
    }
```

## Best Practices

1. **Start with existing gaits** - modify rather than create from scratch
2. **Test incrementally** - small changes, frequent testing  
3. **Use meaningful parameters** - stride in mm, clearance in mm
4. **Document your gait** - what behavior does it create?
5. **Consider robot limits** - don't exceed joint ranges or speeds
6. **Think in phases** - what is each leg doing when?

## Troubleshooting

**Gait doesn't move forward:**
- Check stride parameter is positive
- Verify X-axis movement pattern
- Ensure legs aren't fighting each other

**Robot tips over:**
- Reduce clearance (leg lift height)
- Increase step_size (slower movement)
- Check phase relationships (diagonal legs should alternate)

**Jerky movement:**
- Smaller step_size for smoother motion
- Check for discontinuities in movement patterns
- Verify phase transitions are smooth

**Legs interfere:**
- Check leg coordinate limits
- Add lateral movement if needed
- Verify phase timing prevents collisions