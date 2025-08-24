from settings import settings
import numpy as np
from src.motion.kinematics import QuadrupedKinematics

km = QuadrupedKinematics(settings.coxa_length, settings.femur_length, settings.tibia_length, settings.robot_width, settings.robot_length)

def array_to_dict(ar, row: str = "Leg", col: list = ["x", "y", "z"]):
    ar = np.asarray(ar)
    if ar.ndim == 1:
        # 1D array: map each value to a single column name
        return {f"{row} {i}": {col[0]: float(val)} for i, val in enumerate(ar)}
    elif ar.ndim == 2:
        # 2D array: map each row to all column names
        return {
            f"{row} {i}": {col[j]: float(data[j]) for j in range(min(len(col), len(data)))}
            for i, data in enumerate(ar)
        }
    else:
        raise ValueError("array_to_dict only supports 1D or 2D arrays")

def dict_to_fixed_width_table(data, col_width=10):
    if not data:
        print("Empty dict")
        return

def table(data, row_label="leg", col_label=["coxa", "femur", "tibia"], col_width=10):
    dict_data = array_to_dict(data, row_label, col_label)
    headers = [""] + list(next(iter(dict_data.values())).keys())
    lines = []
    # Header row
    lines.append("".join(f"{h:<{col_width}}" for h in headers))
    # Data rows
    for outer_key, inner_dict in dict_data.items():
        row = [str(outer_key)]
        for h in headers[1:]:
            v = inner_dict.get(h, "")
            if isinstance(v, float):
                v = f"{v:.2f}"
            row.append(str(v))
        lines.append("".join(f"{v:<{col_width}}" for v in row))
    return "\n".join(lines)

ouput = f"""
I am a quadruped robot named Vega. 
I have four legs, each with three joints: coxa, femur, and tibia. 
My coxa joint allows my leg to rotate around a vertical axis, the femur is my upper leg segment, and the tibia is my lower leg segment. 
I can perform various gaits such as walking, trotting, and turning. 
My movements are controlled through precise kinematics calculations to ensure stability and agility.

These are my key attributes:

- Coxa Length: {settings.coxa_length} mm
- Femur Length: {settings.femur_length} mm
- Tibia Length: {settings.tibia_length} mm mm
- Robot Width: {settings.robot_width} mm
- Robot Length: {settings.robot_length} mm

My legs are referenced in an array format as follows:
Legs: [0, 1, 2, 3]  # 0: front-right, 1: front-left, 2: back-left, 3: back-right
    
    L1 - L0
     |   |   
    L2 - L3

Joints per leg: [0, 1, 2]  # 0: coxa, 1: femur, 2: tibia

Tthe following numpy arrays define my physical configuration and control parameters, 
each formatted as a 4x3 matrix where rows correspond to legs and columns to joints:

Initial Joint Angles (radians):
{table(settings.angle_zero)}

Initial Joint Angles (degrees) relative to chain (body -> coxa -> femur -> tibia)
coxa - relative to body
femur - relative to coxa
tibia - relative to femur:
{table(np.degrees(settings.angle_zero))}

Position Offsets (mm) positioning foot relaive to zero position 
used for standing and gaits to make sure feet are in consistent positions relative to body
based on variations in servos:
{table(settings.default_position_offsets)}

Angle Flip to account for servo installation orientation:
{table(settings.angle_flip.reshape(4,3))}

The calculated max body hip height relative to ground legs are fully extended 
and the femur is angled 90 degrees from the coxa (pointing down) is:
{settings.robot_max_height} mm
this is basically the sum of femur and tibia lengths.

The following are key predefined leg positions I use.
The values represent the (x, y, z) coordinates of each foot relative its zero position.
X is forward/backward, Y is left/right, and Z is up/down. Z represents the height of the hip off the ground.

- Home Position legs are pointing straight down and fully extended):
{table(settings.position_home,col_label=["x","y","z"])}

- Ready Position (default walking position knees bent, legs under body):
{table(settings.position_ready,col_label=["x","y","z"])}

- Crouch Position (halfway to ready knees bent more than ready, bringing body lower):
{table(settings.position_crouch, col_label=["x","y","z"])}

- Sit Position (front legs up, back bent leaving the robot in a seated position):
{table(settings.position_sit, col_label=["x","y","z"])}


The calculated angle offsets (in degrees) required to achieve these positions from the zero position are:
- Home Position:
{km.inverse_kinematics_all_legs(settings.position_home, settings.position_offsets, format="degrees")}

- Ready Position:
{km.inverse_kinematics_all_legs(settings.position_ready, settings.position_offsets, format="degrees")}

- Crouch Position:
{km.inverse_kinematics_all_legs(settings.position_crouch, settings.position_offsets, format="degrees")}

- Sit Position:
{km.inverse_kinematics_all_legs(settings.position_sit, settings.position_offsets, format="degrees")}

"""


print(ouput)