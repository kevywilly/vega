# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import adafruit_bno055
import math
from config import ImuOffsets

i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
sensor = adafruit_bno055.BNO055_I2C(i2c)
sensor.offsets_gyroscope = ImuOffsets.gyro
sensor.offsets_magnetometer = ImuOffsets.magnetic
sensor.offsets_accelerometer = ImuOffsets.accel

# If you are going to use UART uncomment these lines
# uart = board.UART()
# sensor = adafruit_bno055.BNO055_UART(uart)

last_val = 0xFFFF


def temperature():
    global last_val  # pylint: disable=global-statement
    result = sensor.temperature
    if abs(result - last_val) == 128:
        result = sensor.temperature
        if abs(result - last_val) == 128:
            return 0b00111111 & result
    last_val = result
    return result


while True:
    print("Temperature: {} degrees C".format(sensor.temperature))
    """
    print(
        "Temperature: {} degrees C".format(temperature())
    )  # Uncomment if using a Raspberry Pi
    """

    x,y,z  = sensor.magnetic
    print("Heading: {}".format(math.atan2(y, x)))
    print("Accelerometer (m/s^2): {}".format(sensor.acceleration))
    print("Magnetometer (microteslas): {}".format(sensor.magnetic))
    print("Gyroscope (rad/sec): {}".format(sensor.gyro))
    print("Euler angle: {}".format(sensor.euler))
    print("Quaternion: {}".format(sensor.quaternion))
    print("Linear acceleration (m/s^2): {}".format(sensor.linear_acceleration))
    print("Gravity (m/s^2): {}".format(sensor.gravity))
    print(f"Calibration: {sensor.calibration_status}")

    a,b,c,d = sensor.calibration_status

    if a+b+c+d == 12:
        print("Insert these preset offset values into project code:")
        print(f"  Offsets_Magnetometer:  {sensor.offsets_magnetometer}")
        print(f"  Offsets_Gyroscope:     {sensor.offsets_gyroscope}")
        print(f"  Offsets_Accelerometer: {sensor.offsets_accelerometer}")
        break

    time.sleep(0.5)

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