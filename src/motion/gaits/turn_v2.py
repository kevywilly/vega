"""
TurnV2 - Improved turning gait using differential/pivot approach.

This gait creates a more effective turn by:
1. Using diagonal leg pairs (trot pattern) for stability
2. Opposite sides push in opposite directions (tank-turn style)
3. Combines forward motion on outer legs with backward on inner legs
4. Faster cycle with only 2 phases instead of 5

Leg layout:
    L0 (FR) --- L1 (FL)
        |           |
    L3 (BR) --- L2 (BL)

For right turn (turn_direction=-1):
  - Left legs (L1, L2) push backward (propel turn)
  - Right legs (L0, L3) push forward (or pivot in place)
  
For left turn (turn_direction=1):
  - Right legs (L0, L3) push backward
  - Left legs (L1, L2) push forward
"""

import numpy as np
from src.motion.gaits.gait import Gait


class TurnV2(Gait):
    """
    Improved pivot turn using trot-style diagonal leg pairs.
    
    Parameters:
        stride: How far each leg moves (larger = sharper turn)
        clearance: Foot lift height
        step_size: Angular resolution (smaller = smoother but slower)
        turn_direction: 1 for left, -1 for right
        pivot_ratio: 0.0 = pure pivot (inner legs stationary), 
                     1.0 = tank turn (inner legs move backward)
                     Default 0.7 for good balance
    """
    
    def __init__(self, pivot_ratio=0.7, **kwargs):
        self.pivot_ratio = pivot_ratio
        super().__init__(**kwargs)
    
    def build_steps(self):
        ns = self.num_steps
        total_steps = ns * 2  # Two phases: diagonal pair A, then diagonal pair B
        
        # Movement magnitudes
        lift = self.clearance
        outer_stride = self.stride  # Outer legs push back to turn
        inner_stride = self.stride * self.pivot_ratio  # Inner legs push forward (or less)
        
        # Smooth motion curves
        # Phase 1: Lift, swing forward/back
        # Phase 2: On ground, push (stance phase)
        swing_out = np.sin(np.radians(np.linspace(0, 180, ns)))  # 0 -> 1 -> 0
        swing_in = np.sin(np.radians(np.linspace(0, 180, ns)))
        lift_curve = np.sin(np.radians(np.linspace(0, 180, ns)))  # Smooth lift
        
        # Stance phase - foot on ground, pushing
        stance_out = np.linspace(1, -1, ns)  # Start at front, push to back
        stance_in = np.linspace(-1, 1, ns)   # Opposite direction
        ground = np.zeros(ns)
        
        # For right turn (turn_direction = -1):
        #   L0 (FR), L2 (BL) = diagonal pair A - outer legs, push back
        #   L1 (FL), L3 (BR) = diagonal pair B - inner legs, push forward/pivot
        # For left turn (turn_direction = 1): swap roles
        
        td = self.turn_direction
        
        # --- Diagonal Pair A: L0 (Front-Right) and L2 (Back-Left) ---
        # These move together in trot pattern
        
        # L0 and L2 are "outer" legs for right turn, "inner" for left turn
        l0_l2_stride = outer_stride if td == -1 else inner_stride
        l0_l2_direction = 1 if td == -1 else -1  # Push direction
        
        # Phase 1: Pair A swings (in air), Phase 2: Pair A in stance (pushing)
        x0 = np.hstack([
            swing_out * l0_l2_stride * l0_l2_direction,  # Swing phase
            stance_out * l0_l2_stride * l0_l2_direction * 0.5  # Stance/push
        ])
        z0 = np.hstack([
            -lift_curve * lift,  # Lift during swing
            ground  # On ground during stance
        ])
        y0 = np.zeros(total_steps)  # No lateral movement
        
        # L2 mirrors L0 for diagonal pair (same timing)
        x2 = x0.copy()
        z2 = z0.copy()
        y2 = np.zeros(total_steps)
        
        # --- Diagonal Pair B: L1 (Front-Left) and L3 (Back-Right) ---
        # Offset by half cycle (opposite phase)
        
        l1_l3_stride = inner_stride if td == -1 else outer_stride
        l1_l3_direction = -1 if td == -1 else 1
        
        # Phase 1: Pair B in stance, Phase 2: Pair B swings
        x1 = np.hstack([
            stance_in * l1_l3_stride * l1_l3_direction * 0.5,  # Stance first
            swing_in * l1_l3_stride * l1_l3_direction  # Then swing
        ])
        z1 = np.hstack([
            ground,  # On ground first
            -lift_curve * lift  # Then lift
        ])
        y1 = np.zeros(total_steps)
        
        # L3 mirrors L1
        x3 = x1.copy()
        z3 = z1.copy()
        y3 = np.zeros(total_steps)
        
        # Reshape into step arrays
        self.steps1 = Gait.reshape_steps(np.array([x0, y0, z0]), total_steps)  # L0 FR
        self.steps2 = Gait.reshape_steps(np.array([x1, y1, z1]), total_steps)  # L1 FL
        self.steps3 = Gait.reshape_steps(np.array([x2, y2, z2]), total_steps)  # L2 BL
        self.steps4 = Gait.reshape_steps(np.array([x3, y3, z3]), total_steps)  # L3 BR

    def get_offsets(self, index) -> np.ndarray:
        """Override to use all 4 independent leg trajectories."""
        return np.array([
            self.steps1[index],
            self.steps2[index], 
            self.steps3[index],
            self.steps4[index]
        ])


class TurnInPlace(Gait):
    """
    Pure pivot turn - rotates in place without forward/backward motion.
    All legs work together to rotate the body around its center.
    
    This creates a yaw rotation by having:
    - Front legs sweep one direction
    - Back legs sweep opposite direction
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def build_steps(self):
        ns = self.num_steps
        total_steps = ns * 2
        
        lift = self.clearance
        arc = self.stride  # Arc length of rotation
        
        td = self.turn_direction
        
        # Lift and sweep curves
        sweep_fwd = np.sin(np.radians(np.linspace(0, 180, ns)))
        sweep_back = np.linspace(1, -1, ns)
        lift_curve = np.sin(np.radians(np.linspace(0, 180, ns)))
        ground = np.zeros(ns)
        
        # Front legs sweep in turn direction (creates yaw)
        # Back legs sweep opposite (also creates yaw, same rotation)
        
        # Diagonal pair A (L0, L2) - swing first
        # Front-Right: Y positive = turn left, so multiply by td
        y0 = np.hstack([sweep_fwd * arc * td, sweep_back * arc * td * 0.5])
        z0 = np.hstack([-lift_curve * lift, ground])
        x0 = np.zeros(total_steps)
        
        # Back-Left: Opposite Y direction for rotation
        y2 = np.hstack([sweep_fwd * arc * (-td), sweep_back * arc * (-td) * 0.5])
        z2 = np.hstack([-lift_curve * lift, ground])
        x2 = np.zeros(total_steps)
        
        # Diagonal pair B (L1, L3) - swing second (offset phase)
        y1 = np.hstack([sweep_back * arc * td * 0.5, sweep_fwd * arc * td])
        z1 = np.hstack([ground, -lift_curve * lift])
        x1 = np.zeros(total_steps)
        
        y3 = np.hstack([sweep_back * arc * (-td) * 0.5, sweep_fwd * arc * (-td)])
        z3 = np.hstack([ground, -lift_curve * lift])
        x3 = np.zeros(total_steps)
        
        self.steps1 = Gait.reshape_steps(np.array([x0, y0, z0]), total_steps)
        self.steps2 = Gait.reshape_steps(np.array([x1, y1, z1]), total_steps)
        self.steps3 = Gait.reshape_steps(np.array([x2, y2, z2]), total_steps)
        self.steps4 = Gait.reshape_steps(np.array([x3, y3, z3]), total_steps)

    def get_offsets(self, index) -> np.ndarray:
        return np.array([
            self.steps1[index],
            self.steps2[index],
            self.steps3[index],
            self.steps4[index]
        ])


# Test
if __name__ == "__main__":
    print("Testing TurnV2...")
    gait = TurnV2(stride=40, clearance=50, step_size=15, turn_direction=-1)
    print(f"Steps shape: {gait.steps1.shape}")
    print(f"Total steps per cycle: {gait.max_index}")
    
    print("\nFirst 5 positions:")
    for i in range(5):
        pos = next(gait)
        print(f"  {i}: {pos}")
    
    # Uncomment to visualize
    # gait.plotit()
