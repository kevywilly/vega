import numpy as np

class Leg:
    def __init__(self, name, femur_length, tibia_length):
        self.name = name
        self.femur_length = femur_length
        self.tibia_length = tibia_length
        # Initialize leg parameters (angles, positions, etc.)

    def move(self, femur_angle, tibia_angle):
        # Calculate joint positions based on angles and leg geometry
        # Move the leg segments accordingly
        print(f"{self.name}: Femur Angle: {np.degrees(femur_angle)}, Tibia Angle: {np.degrees(tibia_angle)}")


class Quadruped:
    def __init__(self, leg_params):
        self.legs = []
        for params in leg_params:
            name, femur_length, tibia_length = params
            self.legs.append(Leg(name, femur_length, tibia_length))

    def trot_gait(self, cycle_time):
        # Calculate joint angles for trot gait
        # Implement coordination between legs for stability
        time_periods = np.linspace(0, 2 * np.pi, cycle_time, endpoint=False)
        for t in time_periods:
            femur_angle = np.sin(t)
            tibia_angle = np.sin(t + np.pi / 2)
            for leg in self.legs:
                leg.move(femur_angle, tibia_angle)
            # Adjust timings for synchronization between diagonal legs

# Example usage
leg_params = [("Front Left", 102, 114), ("Front Right", 102, 114), ("Back Left", 102, 114), ("Back Right", 102, 114)]
spot = Quadruped(leg_params)
spot.trot_gait(cycle_time=10)