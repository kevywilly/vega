"""
Prowl Gait - Stealthy, deliberate movement for the quadruped robot.

This gait mimics the stalking movement of big cats:
- Lower to the ground (crouched posture)
- Longer ground contact phases (more stable)
- Diagonal leg coordination (proven stable from trot)
- Subtle hip sway for natural weight shifting

Based on the proven trot pattern with modifications for slower,
more deliberate movement.
"""

import numpy as np

from settings import settings
from src.motion.gaits.gait import Gait
from src.motion.gaits.gait_params import GaitParams


class Prowl(Gait):
    """
    Stealthy prowling gait with diagonal leg coordination.

    Key differences from Trot:
    - Lower clearance (crouched movement)
    - Modified lift pattern with longer ground contact
    - Subtle hip sway for weight shifting
    - Smoother stride transitions
    """

    def build_steps(self):
        # Forward/backward movement - same smooth pattern as trot
        # but the physical effect is slower due to longer ground contact
        x = np.hstack([
            self.stride_forward(),
            self.stride_home(),
            self.stride_back(self.num_steps * 2),
        ]) * int(self.stride)

        # Hip sway for natural weight shifting during prowl
        # Amplitude varies through the cycle:
        # - Higher during swing phase (weight shift to standing legs)
        # - Lower during stance phase
        y = self._prowl_hip_sway()

        # Vertical movement - prowl-specific pattern
        # Key: longer ground contact, quick but low lift
        z = self._prowl_lift_pattern() * (-self.clearance)

        # Build step sequences for diagonal pair 1 (legs 0, 2)
        self.steps1 = Gait.reshape_steps(np.array([x, y, z]), self.num_steps * 4)

        # Diagonal pair 2 (legs 1, 3) - 50% phase offset, opposite hip sway
        steps2_x = np.roll(x, self.num_steps * 2)
        steps2_y = -np.roll(y, self.num_steps * 2)  # Opposite for balance
        steps2_z = np.roll(z, self.num_steps * 2)

        self.steps2 = Gait.reshape_steps(
            np.array([steps2_x, steps2_y, steps2_z]),
            self.num_steps * 4
        )

    def _prowl_lift_pattern(self) -> np.ndarray:
        """
        Create a prowl-specific lift pattern.

        Unlike trot which lifts during the first num_steps then stays down,
        prowl has a quicker, lower lift to keep the robot crouched and stable.

        Pattern breakdown (total = num_steps * 4):
        - Phase 1 (num_steps): Quick lift and return - the "step"
        - Phase 2-4 (num_steps * 3): On ground - long stance phase

        This gives ~75% ground contact vs trot's ~75%, but the lift
        is shaped differently for smoother, more deliberate movement.
        """
        # Quick lift phase - use a compressed sine for snappier foot placement
        lift_steps = self.num_steps

        # Modified lift: start from ground, quick up, controlled down
        # Using a sine curve from 0 to pi for smooth up-and-down
        lift = np.sin(np.linspace(0, np.pi, lift_steps))

        # Scale the lift to be lower than normal (prowl is crouched)
        # The clearance parameter is already reduced, but we can further
        # modify the curve shape for a "sneakier" feel
        lift = lift * 0.85  # Slightly lower peak

        # Long ground contact phase
        ground = np.zeros(self.num_steps * 3)

        return np.hstack([lift, ground])

    def _prowl_hip_sway(self) -> np.ndarray:
        """
        Create hip sway pattern for weight shifting during prowl.

        The sway helps shift weight to the standing diagonal pair
        when the other pair is lifted. This improves stability
        during the slow, deliberate movement.

        Pattern:
        - During swing (lift): shift weight away from lifting legs
        - During stance: subtle sway for natural movement
        """
        # During lift phase: stronger sway to shift weight
        swing_sway = np.sin(np.linspace(0, np.pi, self.num_steps)) * 0.6

        # During first part of stance: return to center
        return_sway = np.sin(np.linspace(np.pi, 2*np.pi, self.num_steps)) * 0.3

        # During rest of stance: minimal movement for stability
        stance_sway = np.sin(np.linspace(0, np.pi, self.num_steps * 2)) * 0.15

        return np.hstack([swing_sway, return_sway, stance_sway]) * self.hip_sway


class ProwlParams(GaitParams):
    """
    Recommended parameters for prowl gait.

    Compared to default trot params:
    - Lower clearance (crouched)
    - Smaller stride (deliberate steps)
    - Same step_size (controls speed via controller frequency)
    """
    stride: int = 40  # Shorter steps for deliberate movement
    clearance: int = 35  # Lower to ground (vs 65 for trot)
    step_size: int = 15  # Same timing resolution
    hip_sway: int = 8  # Slightly more sway for weight shifting


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # Test visualization
    params = ProwlParams()
    gait = Prowl(
        p0=settings.position_ready,
        params=params
    )

    print(f"Prowl gait created:")
    print(f"  - Stride: {params.stride}mm")
    print(f"  - Clearance: {params.clearance}mm")
    print(f"  - Steps per cycle: {gait.num_steps * 4}")
    print(f"  - Hip sway: {params.hip_sway}mm")

    # Plot step sequences
    print("\nDiagonal pair 1 (legs 0, 2):")
    plt.figure(figsize=(12, 4))
    plt.plot(gait.steps1, label=["x (forward)", "y (lateral)", "z (lift)"])
    plt.legend()
    plt.title("Prowl - Diagonal Pair 1 (legs 0, 2)")
    plt.xlabel("Step index")
    plt.ylabel("Offset (mm)")
    plt.grid(True, alpha=0.3)
    plt.show()

    print("\nDiagonal pair 2 (legs 1, 3):")
    plt.figure(figsize=(12, 4))
    plt.plot(gait.steps2, label=["x (forward)", "y (lateral)", "z (lift)"])
    plt.legend()
    plt.title("Prowl - Diagonal Pair 2 (legs 1, 3)")
    plt.xlabel("Step index")
    plt.ylabel("Offset (mm)")
    plt.grid(True, alpha=0.3)
    plt.show()

    # Show phase relationship
    print("\nPhase comparison (z-axis lift):")
    plt.figure(figsize=(12, 4))
    plt.plot(gait.steps1[:, 2], label="Pair 1 (legs 0,2)", linewidth=2)
    plt.plot(gait.steps2[:, 2], label="Pair 2 (legs 1,3)", linewidth=2)
    plt.legend()
    plt.title("Prowl - Lift Phase Relationship (50% offset)")
    plt.xlabel("Step index")
    plt.ylabel("Z offset (mm)")
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
    plt.show()
