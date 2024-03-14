import numpy as np
from src.vision.sensors import CameraSensor
serial_port = '/dev/serial0'

SERVOS = np.array([[11, 12, 13], [21, 22, 23], [31, 32, 33], [41, 42, 43]])
SERVO_IDS = SERVOS.reshape(-1)
# FLIP = np.array([[1, 0.9, 1.1], [-1, -0.9, -1.1], [-1, -1.1, -0.9], [1, 1.1, 0.9]])
FLIP = np.array([[1, 1, 1], [-1, -1, -1], [-1, -1, -1], [1, 1, 1]])

POSITION_OFFSETS = np.array([
    [0,0,0],
    [0,0,0],
    [0,0,10],
    [0,0,10]
])

DEFAULT_SENSOR_MODE = CameraSensor.MODE1640x1232X29

CAMERA_MATRIX = np.array([
            848.72138, 0., 939.50914,
            0., 848.9676 , 596.15355,
            0., 0., 1.
]).reshape(3,3)

DISTORTION_COEFFICIENTS = np.array([-0.296850, 0.061372, 0.002562, -0.002645, 0.000000]).reshape(1,5)
DEBUG = True

class Dims:
    coxa = 53
    femur = 102
    tibia = 114
    max_height = femur + tibia
    lengths = np.array([coxa, femur, tibia])


class Angles:
    zero = np.radians(np.array([[2, 90, 30], [2, 90, 30], [2, 90, 30], [2, 90, 30]]))


class Positions:
    home = np.array([[0, 0, Dims.max_height], [0, 0, Dims.max_height], [0, 0, Dims.max_height], [0, 0, Dims.max_height]])
    ready = home * 0.75
    crouch = home * 0.33
    step = ready + ([[0,50,-40],[0,0,0],[0,0,0],[0,0,0]])
