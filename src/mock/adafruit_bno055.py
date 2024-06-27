from typing import Any


class BNO055_I2C:
    def __init__(self, i2c: Any):
        self.i2c = i2c
        self.mode = 0x0C
        self.axis_remap = (0, 1, 2, 1, 0, 1)
        self.offsets_gyroscope = (0, 0, 0)
        self.offsets_magnetometer = (0, 0, 0)
        self.offsets_accelerometer = (0, 0, 0)

        self.acceleration = (0.0, 0.0, 0.0)
        self.magnetic = (0.0, 0.0, 0.0)
        self.gyro = (0.0, 0.0, 0.0)
        self.euler = (180, 0.0, 0.0)
        self.quaternion = (0.0, 0.0, 0.0, 0.0)
        self.linear_acceleration = (0.0, 0.0, 0.0)
        self.gravity = (0.0, 0.0, 0.0)
