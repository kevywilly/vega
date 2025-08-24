import numpy as np

from settings import settings
from src.motion.gaits.gait import Gait


class TrotWithLateral(Gait):
    """
    Trot gait with minimal lateral hip (coxa) movement for improved stability and naturalness.
    
    This gait adds small lateral movements in the y-axis that create coxa joint rotation,
    helping to shift weight and improve the gait dynamics while maintaining the basic trot pattern.
    """

    def __init__(self, lateral_amplitude=8, **kwargs):
        """
        Initialize trot with lateral movement.
        
        Args:
            lateral_amplitude: Maximum lateral movement in mm (default: 8mm)
            **kwargs: Standard gait parameters (stride, clearance, step_size, etc.)
        """
        self.lateral_amplitude = lateral_amplitude
        super().__init__(**kwargs)

    def build_steps(self):
        # Forward/backward movement (same as regular trot)
        x = np.hstack([
            self.stride_forward(),
            self.stride_home(),
            self.stride_back(self.num_steps * 2),
        ]) * int(self.stride)

        # Lateral movement - small sinusoidal motion to engage coxa
        # Create a gentle lateral sway that's synchronized with the gait cycle
        lateral_pattern = np.hstack([
            # During lift phase: slight lateral movement to help with weight shift
            np.sin(np.linspace(0, np.pi, self.num_steps)) * 0.7,  # Gentle outward movement during lift
            # During stance phase: minimal lateral movement
            np.sin(np.linspace(np.pi, 2*np.pi, self.num_steps)) * 0.3,  # Small inward movement during stance
            # Ground contact phase: return to neutral
            np.sin(np.linspace(0, np.pi, self.num_steps * 2)) * 0.2,  # Very minimal movement during ground phase
        ])
        
        y = lateral_pattern * self.lateral_amplitude

        # Vertical movement (same as regular trot)
        z = np.hstack([
            self.downupdown(),
            np.repeat(self.zeros, 3),
        ]) * (-self.clearance)

        # Build step sequences
        self.steps1 = Gait.reshape_steps(np.array([x, y, z]), self.num_steps * 4)
        
        # Phase shift for diagonal gait pattern, but with opposite lateral movement
        # This creates the natural hip sway where diagonal legs move in opposite lateral directions
        steps2_x = np.roll(x, self.num_steps * 2)
        steps2_y = -np.roll(y, self.num_steps * 2)  # Opposite lateral movement for diagonal legs
        steps2_z = np.roll(z, self.num_steps * 2)
        
        self.steps2 = Gait.reshape_steps(np.array([steps2_x, steps2_y, steps2_z]), self.num_steps * 4)


if __name__ == "__main__":
    # Test the gait
    gait = TrotWithLateral(
        p0=settings.position_ready,
        stride=50,
        clearance=50,
        step_size=15,
        lateral_amplitude=6  # 6mm lateral movement
    )

    print(f"Gait size: {gait.size}")
    print(f"Gait shape: {gait.shape}")
    
    # Show the lateral movement pattern
    print("Lateral movement range for leg 1:", np.min(gait.steps1[:, 1]), "to", np.max(gait.steps1[:, 1]))
    print("Lateral movement range for leg 2:", np.min(gait.steps2[:, 1]), "to", np.max(gait.steps2[:, 1]))

    # Uncomment to visualize
    gait.plotit()