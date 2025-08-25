import os
from enum import Enum
from functools import cached_property
from typing import Tuple, Dict, List, Optional

import numpy as np
import yaml

from src.model.tilt import Tilt
from src.vision.sensors import CameraSensorMode

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

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = os.environ.get(
    "VEGA_CONFIG_FILE", os.path.join(ROOT_DIR, "settings.yml")
)


def load_settings():
    filename = CONFIG_FILE_PATH
    with open(filename, "r") as f:
        return yaml.safe_load(f)


class LegGroup(List, Enum):
    front = [0, 1]
    back = [2, 3]
    left = [1, 2]
    right = [0, 3]
    all = [0, 1, 2, 3]


class Settings:
    def __init__(self, config: Optional[Dict] = {}):
        self.debug: str = config.get("debug", False)
        self.environment: str = os.environ.get(
            "VEGA_ENVIRONMENT", config.get("environment", "development")
        )
        self.api_url: str = os.environ.get(
            "VEGA_API_URL", config.get("api_url", "http://localhost:5000/api")
        )
        self.serial_port: str = os.environ.get(
            "SERIAL_PORT", config.get("serial_port", "/dev/serial0")
        )

        self.servos: np.ndarray = np.array(config.get("servos", []))

        # sensors
        _sensors = config.get("sensors", {})
        _camera = _sensors.get("camera", {})

        self.default_sensor_mode: CameraSensorMode = CameraSensorMode[
            _camera.get("sensor_mode")
        ]
        self.camera_matrix: np.ndarray = np.array(_camera.get("matrix", None)).reshape(
            3, 3
        )
        self.distortion_coefficients: np.ndarray = np.array(
            _camera.get("distortion", None)
        ).reshape(1, 5)
        # imu

        _imu = config.get("imu", {})
        _imu_offsets = _imu.get("offsets", {})

        self.bno_axis_remap: Optional[Tuple] = _imu.get(
            "bno_axis_remap", None
        )  # (0, 1, 2, 1, 0, 1)
        self.imu_magnetic_offsets: Optional[Tuple[int, int, int]] = _imu_offsets.get(
            "magnetic"
        )
        self.imu_gyro_offsets: Optional[Tuple[int, int, int]] = _imu_offsets.get("gyro")
        self.imu_acceleration_offsets: Optional[Tuple[int, int, int]] = (
            _imu_offsets.get("acceleration")
        )

        # Dimensions (mm)

        _dimensions = config.get("dims", {})

        self.robot_width: int = _dimensions.get("robot_width", 142)
        self.robot_length: int = _dimensions.get("robot_length", 223)
        self.coxa_length: int = _dimensions.get("coxa_length", 53)
        self.femur_length: int = _dimensions.get("femur_length", 102)
        self.tibia_length: int = _dimensions.get("tibia_length", 114)

        # Leveling

        _leveling = config.get("leveling", {})

        self.yaw_threshold: float = _leveling.get("yaw_threshold", 0.5)
        self.pitch_threshold: float = _leveling.get("pitch_threshold", 0.5)
        self.auto_level: bool = _leveling.get("auto_level", False)
        self.tilt: Tilt = Tilt(**_leveling.get("tilt", {}))

        # Positioning

        _positioning = config.get("positioning", {})

        self.angle_flip: np.ndarray = np.array(
            _positioning.get("angle_flip", np.ones((4, 3)))
        ).astype(int)

        self.angle_zero: np.ndarray = np.radians(
            np.array(_positioning.get("angle_zero"))
        )

        self.default_position_offsets = np.array(_positioning.get("offsets")).astype(
            int
        )

        self.position_offsets: np.ndarray = np.copy(self.default_position_offsets)

        self.position_forward_offsets = np.array(
            _positioning.get("forward_offsets", np.zeros(3))
        ).astype(int)

        self.position_backward_offsets = np.array(
            _positioning.get("backward_offsets", np.zeros(3))
        ).astype(int)
        
        self.position_ready_height_pct: float = _positioning.get(
            "ready_height_pct", 0.5
        )

        # Gait Parameters

        _gait_params = config.get("gait_params", {})

        self.trot_params: Dict[str, int] = _gait_params.get("trot", {})
        self.trot_reverse_params: Dict[str, int] = _gait_params.get("trot_reverse", {})
        self.sidestep_params: Dict[str, int] = _gait_params.get("sidestep", {})
        self.turn_params: Dict[str, int] = _gait_params.get("turn", {})
        self.walk_params: Dict[str, int] = _gait_params.get("walk", {})
        self.trot_in_place_params: Dict[str, int] = _gait_params.get(
            "trot_in_place", {"stride": 0, "clearance": 40, "step_size": 25}
        )

    @cached_property
    def servo_ids(self) -> np.ndarray:
        return self.servos.reshape(-1)

    @cached_property
    def robot_max_height(self) -> int:
        return self.femur_length + self.tibia_length

    @cached_property
    def joint_lengths(self) -> np.ndarray:
        return np.array([self.coxa_length, self.femur_length, self.tibia_length])

    @cached_property
    def position_home(self) -> np.ndarray:
        return np.zeros((4, 3)).astype(np.float16) + [0, 0, self.robot_max_height]

    @cached_property
    def position_ready(self) -> np.ndarray:
        ar = self.position_home * self.position_ready_height_pct
        ar[:, 2] *= [0.9, 0.9, 1, 1]
        return ar.astype(int)

    @cached_property
    def position_crouch(self) -> np.ndarray:
        return self.position_ready * 0.7

    @cached_property
    def position_sit(self) -> np.ndarray:
        ar = self.position_home * 1
        ar[:, 2] *= [0.8, 0.8, 0.2, 0.2]
        ar[:, 0] += [10, 10, -25, -35]
        return ar.astype(int)
    
    @cached_property
    def position_walk(self) -> np.ndarray:
        ar = self.position_home * self.position_ready_height_pct
        ar[:, 2] *= [0.8, 0.8, 1, 1]
        return ar.astype(int)

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


settings = Settings(load_settings())
