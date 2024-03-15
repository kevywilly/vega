import atexit
import math

import adafruit_bno055
import board
import numpy as np
import traitlets

from src.nodes.node import Node


class IMU(Node):
    acceleration = traitlets.Any()
    magnetic = traitlets.Any()
    gyro = traitlets.Any()
    euler = traitlets.Any()
    quaternion = traitlets.Any()
    linear_acceleration = traitlets.Any()
    gravity = traitlets.Any()

    def __init__(self, *args, **kwargs):
        super(IMU, self).__init__(*args, **kwargs)
        self.sensor = adafruit_bno055.BNO055_I2C(board.I2C())
        self.sensor.offsets_gyroscope = ImuOffsets.gyro
        self.sensor.offsets_magnetometer = ImuOffsets.magnetic
        self.sensor.offsets_accelerometer = ImuOffsets.accel
        self.read_measurements()

        atexit.register(self.shutdown)

    def read_measurements(self):
        self.acceleration = np.array(self.sensor.acceleration)
        self.magnetic = np.array(self.sensor.magnetic)
        self.gyro = np.array(self.sensor.gyro)
        self.euler = np.array(self.sensor.euler)
        self.quaternion = np.array(self.sensor.quaternion)
        self.linear_acceleration = np.array(self.sensor.linear_acceleration)
        self.gravity = np.array(self.sensor.gravity)


    def spinner(self):
        self.read_measurements()
