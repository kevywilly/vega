import os
from enum import Enum
from functools import cached_property
from typing import Tuple, Dict, List, Optional

import numpy as np

from src.model.tilt import Tilt
from src.vision.sensors import CameraSensor

"""
    L1 - L0
     |   |   
    L2 - L3
"""


# BNO sensor axes remap values.  These are the parameters to the BNO.set_axis_remap
# function.  Don't change these without consulting section 3.4 of the datasheet.
# The default axes mapping below assumes the Adafruit BNO055 breakout is flat on
# a table with the row of SDA, SCL, GND, VIN, etc. pins facing away from you.
# BNO_AXIS_REMAP = { 'x': BNO055.AXIS_REMAP_X,
#                    'y': BNO055.AXIS_REMAP_Y,
#                    'z': BNO055.AXIS_REMAP_Z,
#                    'x_sign': BNO055.AXIS_REMAP_POSITIVE,
#                    'y_sign': BNO055.AXIS_REMAP_POSITIVE,
#                    'z_sign': BNO055.AXIS_REMAP_POSITIVE
#                    }

# BNO_AXIS_REMAP = (0,1,2,0,0,0)

class LegGroup(List, Enum):
    front = [0, 1]
    back = [2, 3]
    left = [1, 2]
    right = [0, 3]
    all = [0, 1, 2, 3]


class Settings:
    debug: str = os.environ.get("VEGA_DEBUT", True)

    environment: str = os.environ.get("VEGA_ENVIRONMENT", "development")
    api_url: str = os.environ.get("VEGA_API_URL", "http://localhost:5000/api")
    serial_port: str = os.environ.get("SERIAL_PORT", "/dev/serial0")

    bno_axis_remap: Optional[Tuple] = None  # (0, 1, 2, 1, 0, 1)
    servos: np.ndarray = np.array([[11, 12, 13], [21, 22, 23], [31, 32, 33], [41, 42, 43]])

    @property
    def servo_ids(self) -> np.ndarray:
        return self.servos.reshape(-1)

    #flip_v10: np.ndarray = np.array([[1, 1, 1], [-1, -1, -1], [-1, -1, -1], [1, 1, 1]])
    flip: np.ndarray = np.array([[-1, 1, 1], [-1, -1, -1], [-1, -1, -1], [-1, 1, 1]])

    default_sensor_mode: CameraSensor = CameraSensor.MODE1640x1232X29

    # Camera
    camera_matrix: np.ndarray = np.array([
        848.72138, 0., 939.50914,
        0., 848.9676, 596.15355,
        0., 0., 1.
    ]).reshape(3, 3)

    distortion_coefficients: np.ndarray = np.array([-0.296850, 0.061372, 0.002562, -0.002645, 0.000000]).reshape(1, 5)

    # IMU
    # imu_magnetic_offsets: Tuple[int, int, int] = (419, -250, -597)
    # imu_gyro_offsets: Tuple[int, int, int] = (0, -2, -1)
    # imu_accel_offsets: Tuple[int, int, int] = (16, -31, 14)

    imu_magnetic_offsets = (32418, 32685, -32271)
    imu_gyro_offsets = (0, -1, 0)
    imu_accel_offsets = (-40, 42, -18)

    yaw_threshold: float = 0.5
    pitch_threshold: float = 0.5

    # Dimensions
    robot_width: int = 142
    robot_length: int = 223
    coxa_length: int = 53
    femur_length: int = 102
    tibia_length: int = 114

    @cached_property
    def robot_max_height(self) -> int:
        return self.femur_length + self.tibia_length

    @cached_property
    def joint_lengths(self) -> np.ndarray:
        return np.array([self.coxa_length, self.femur_length, self.tibia_length])

    angles_zero: np.ndarray = np.radians(np.array([[-2, 90, 30], [-2, 90, 30], [2, 90, 30], [2, 90, 30]]))

    default_position_offsets: np.ndarray = np.zeros((4, 3)).astype(int)
    position_offsets: np.ndarray = np.zeros((4, 3)).astype(int)

    position_ready_height_pct: float = 0.65
    position_forward_offsets: np.ndarray = np.array([
        [-10, 0, 0]
    ])

    position_backward_offsets: np.ndarray = np.array([
        [5, 0, 0]
    ])

    @cached_property
    def position_home(self) -> np.ndarray:
        return np.zeros((4, 3)).astype(np.float16) + [0, 0, self.robot_max_height]

    @cached_property
    def position_ready(self) -> np.ndarray:
        return self.position_home * self.position_ready_height_pct

    @cached_property
    def position_crouch(self) -> np.ndarray:
        return self.position_ready * 0.5

    @cached_property
    def position_sit(self) -> np.ndarray:
        ar = self.position_home * 1
        ar[:, 2] *= [0.8, 0.8, 0.2, 0.2]
        ar[:, 0] += [10, 10, -25, -35]
        return ar.astype(int)

    trot_params: Dict[str, int] = {"stride": 46, "clearance": 60, "step_size": 15}
    trot_reverse_params: Dict[str, int] = {"stride": -30, "clearance": 40, "step_size": 15}
    sidestep_params: Dict[str, int] = {"stride": 20, "clearance": 30, "step_size": 15}
    turn_params: Dict[str, int] = {"stride": 10, "clearance": 40, "step_size": 15}

    def adjust_offsets(self, x: int = 0, y: int = 0, z: int = 0, group=None):
        if group is None:
            group = LegGroup.all

        if group == LegGroup.all:
            self.position_offsets += np.array([x, y, z])
        else:
            for idx in group.value:
                self.position_offsets[idx, :] += np.array([x, y, z])

    def reset_offsets(self):
        self.position_offsets = self.default_position_offsets

    auto_level: bool = True

    tilt: Tilt = Tilt()


settings = Settings()
