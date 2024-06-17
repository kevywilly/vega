import atexit

try:
    import adafruit_bno055
    import board
except:
    from src.mock import adafruit_bno055
    from src.mock.board import board

import numpy as np
import traitlets
from config import ImuOffsets, BNO_AXIS_REMAP
from src.nodes.node import Node


class IMUMode:
    CONFIG_MODE = 0x00
    ACCONLY_MODE = 0x01
    MAGONLY_MODE = 0x02
    GYRONLY_MODE = 0x03
    ACCMAG_MODE = 0x04
    ACCGYRO_MODE = 0x05
    MAGGYRO_MODE = 0x06
    AMG_MODE = 0x07
    IMUPLUS_MODE = 0x08
    COMPASS_MODE = 0x09
    M4G_MODE = 0x0A
    NDOF_FMC_OFF_MODE = 0x0B
    NDOF_MODE = 0x0C


class IMU(Node):
    acceleration = traitlets.Any()
    magnetic = traitlets.Any()
    gyro = traitlets.Any()
    euler = traitlets.Any()
    quaternion = traitlets.Any()
    linear_acceleration = traitlets.Any()
    gravity = traitlets.Any()

    def __init__(self, **kwargs):
        super(IMU, self).__init__(**kwargs)
        self.sensor = adafruit_bno055.BNO055_I2C(board.I2C())
        self.sensor.mode = IMUMode.NDOF_MODE
        self.sensor.axis_remap = BNO_AXIS_REMAP
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
