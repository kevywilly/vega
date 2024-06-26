import os

import numpy as np

from src.vision.sensors import CameraSensor

VEGA_ENVIRONMENT = os.environ.get("VEGA_ENVIRONMENT", "development")
VEGA_API_URL = os.environ.get("VEGA_API_URL", "http://localhost:5000/api")
SERIAL_PORT = os.environ.get("SERIAL_PORT", "/dev/serial0")

# BNO sensor axes remap values.  These are the parameters to the BNO.set_axis_remap
# function.  Don't change these without consulting section 3.4 of the datasheet.
# The default axes mapping below assumes the Adafruit BNO055 breakout is flat on
# a table with the row of SDA, SCL, GND, VIN, etc pins facing away from you.
# BNO_AXIS_REMAP = { 'x': BNO055.AXIS_REMAP_X,
#                    'y': BNO055.AXIS_REMAP_Y,
#                    'z': BNO055.AXIS_REMAP_Z,
#                    'x_sign': BNO055.AXIS_REMAP_POSITIVE,
#                    'y_sign': BNO055.AXIS_REMAP_POSITIVE,
#                    'z_sign': BNO055.AXIS_REMAP_POSITIVE
#                    }

# BNO_AXIS_REMAP = (0,1,2,0,0,0)


DEBUG = False

BNO_AXIS_REMAP = (0, 1, 2, 1, 0, 1)
SERVOS = np.array([[11, 12, 13], [21, 22, 23], [31, 32, 33], [41, 42, 43]])
SERVO_IDS = SERVOS.reshape(-1)
FLIP = np.array([[-1, 1, 1], [-1, -1, -1], [-1, -1, -1], [-1, 1, 1]])
DEFAULT_SENSOR_MODE = CameraSensor.MODE1640x1232X29
CAMERA_MATRIX = np.array([
    848.72138, 0., 939.50914,
    0., 848.9676, 596.15355,
    0., 0., 1.
]).reshape(3, 3)
DISTORTION_COEFFICIENTS = np.array([-0.296850, 0.061372, 0.002562, -0.002645, 0.000000]).reshape(1, 5)


class IMU_OFFSETS:
    MAGNETIC = (419, -250, -597)
    GYRO = (0, -2, -1)
    ACCEL = (16, -31, 14)


class DIMS:
    WIDTH = 142
    LENGTH = 252
    COXA = 53
    FEMUR = 102
    TIBIA = 114
    MAX_HEIGHT = FEMUR + TIBIA
    LENGTHS = np.array([COXA, FEMUR, TIBIA])


class ANGLES:
    ZERO = np.radians(np.array([[-2, 90, 30], [-2, 90, 30], [2, 90, 30], [2, 90, 30]]))


class POSITIONS:
    OFFSETS = np.zeros((4, 3)).astype(np.int16)

    HOME = np.zeros((4, 3)).astype(np.float16) + [0, 0, DIMS.MAX_HEIGHT]
    READY = HOME * 0.65 + OFFSETS + np.array([
        [10, 0, 0],
        [10, 0, 0],
        [10, 0, 0],
        [10, 0, 0]
    ])

#    READY = HOME

    READY_REVERSE = HOME * 0.65 + OFFSETS + np.array([
        [-10, 0, 0],
        [-10, 0, 0],
        [-10, 0, 0],
        [-10, 0, 0]
    ])

    CROUCH = READY / 2

    @classmethod
    def reset(cls):
        cls.OFFSETS = np.zeros((4, 3))


trot_params = {"stride": 40, "clearance": 60, "step_size": 15}
sidestep_params = {"stride": 25, "clearance": 30, "step_size": 15}
turn_params = {"degrees": 20, "clearance": 60, "step_size": 10}



