import numpy as np

serial_port = '/dev/serial0'

SERVOS = np.array([[11, 12, 13], [21, 22, 23], [31, 32, 33], [41, 42, 43]])
SERVO_IDS = SERVOS.reshape(-1)
FLIP = np.array([[1, 1, 1], [-1, -1, -1], [-1, -1, -1], [1, 1, 1]])


DEBUG = True

class Dims:
    coxa = 53
    femur = 102
    tibia = 114
    max_height = femur + tibia
    lengths = np.array([coxa, femur, tibia])


class Angles:
    zero = np.radians(np.array([[0, 90, 30], [0, 90, 30], [0, 90, 30], [0, 90, 30]]))


class Positions:
    home = np.array([[0, 0, Dims.max_height], [0, 0, Dims.max_height], [0, 0, Dims.max_height], [0, 0, Dims.max_height]])
    ready = home * 0.75
    crouch = home * 0.33
