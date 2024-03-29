import numpy as np
from src.vision.sensors import CameraSensor
serial_port = '/dev/serial0'


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

BNO_AXIS_REMAP = (0,1,2,1,0,1)

                   
SERVOS = np.array([[11, 12, 13], [21, 22, 23], [31, 32, 33], [41, 42, 43]])
SERVO_IDS = SERVOS.reshape(-1)
FLIP = np.array([[1, 1, 1], [-1, -1, -1], [-1, -1, -1], [1, 1, 1]])



DEFAULT_SENSOR_MODE = CameraSensor.MODE1640x1232X29

CAMERA_MATRIX = np.array([
            848.72138, 0., 939.50914,
            0., 848.9676 , 596.15355,
            0., 0., 1.
]).reshape(3,3)

DISTORTION_COEFFICIENTS = np.array([-0.296850, 0.061372, 0.002562, -0.002645, 0.000000]).reshape(1,5)
DEBUG = True


class ImuOffsets:
    magnetic = (419, -250, -597)
    gyro = (0, -2, -1)
    accel = (16, -31, 14)


class Dims:
    width = 142
    length = 252
    coxa = 53
    femur = 102
    tibia = 114
    max_height = femur + tibia
    lengths = np.array([coxa, femur, tibia])


class Angles:
    zero = np.radians(np.array([[0, 90, 30], [0, 90, 30], [0, 90, 30], [0, 90, 30]]))


class Positions:

    home = np.zeros((4,3)).astype(np.float16) + [0, 0, Dims.max_height]
    ready = home * 0.6 + [20.0, 10.0, 0.0]
    ready2 = home * 0.6 + [20.0, 5.0, 0.0]
    crouch = ready / 2



POSITION_OFFSETS = np.array([
    [0,0,0],
    [0,0,0],
    [0,0,0],
    [0,0,0]
])