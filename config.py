import numpy as np

serial_port = '/dev/serial0'

servos = np.array([[11, 12, 13], [21, 22, 23], [31, 32, 33], [41, 42, 43]])
servo_ids = servos.reshape(-1)
flip = np.array([[1, 1, 1], [-1, -1, -1], [-1, -1, -1], [1, 1, 1]])


class Dims:
    coxa = 50
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
