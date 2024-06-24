# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import adafruit_bno055
from config import BNO_AXIS_REMAP
from src.nodes.imu import IMUMode

i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
sensor = adafruit_bno055.BNO055_I2C(i2c)
sensor.mode = IMUMode.NDOF_MODE
sensor.axis_remap = BNO_AXIS_REMAP

while not sensor.calibrated:

    status = sensor.calibration_status
    print(f"Calibration: {status}")
    a,b,c,d = status

    time.sleep(1)

print("Insert these preset offset values into project code:")
print(f"\tmagnetic = {sensor.offsets_magnetometer}")
print(f"\tgyro = {sensor.offsets_gyroscope}")
print(f"\taccel = {sensor.offsets_accelerometer}")

"""
Offsets_Magnetometer:  (-264, 32413, -32064)
  Offsets_Gyroscope:     (-1, 2, 0)
  Offsets_Accelerometer: (134, -21, -21)

"""

"""
  Offsets_Magnetometer:  (-274, 32389, -32061)
  Offsets_Gyroscope:     (-1, -2, 1)
  Offsets_Accelerometer: (-10, -6, -13)

"""

"""
Offsets_Magnetometer:  (-288, 32420, 674)
  Offsets_Gyroscope:     (-1, -2, 1)
  Offsets_Accelerometer: (-12, -3, -7)

"""