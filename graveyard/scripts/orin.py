import serial
import adafruit_bno055
from src.motion.servo_controller import ServoController
from settings import settings
import busio
import time
import board

ser = serial.Serial('/dev/ttyTHS1')
controller = ServoController(ser)

# Test it
positions = controller.get_positions(settings.servo_ids)
print(positions)

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

def test_controller():
    ser = serial.Serial('/dev/ttyTHS1')
    controller = ServoController(ser)

    # Test it
    positions = controller.get_positions(settings.servo_ids)
    print(positions)
    ser.close()

def test_imu():
    i2c = busio.I2C(board.SCL, board.SDA)  # might need to try different pins

    imu = adafruit_bno055.BNO055_I2C(i2c)
    imu.mode = IMUMode.NDOF_MODE

    remap = imu.axis_remap

    imu.axis_remap = (0, 1, 2, 1, 1, 0)  # Example remap    


    print(remap)

    while True:
        print(f"Euler: {imu.euler}")
        print(f"Quaternion: {imu.quaternion}")
        print(f"Calibration: {imu.calibration_status}")
        print("---")
        time.sleep(0.5)

def test_bno055_chip_id():
    from smbus2 import SMBus

    BNO055_ADDR = 0x28
    BNO055_CHIP_ID_REG = 0x00

    with SMBus(7) as bus:
        chip_id = bus.read_byte_data(BNO055_ADDR, BNO055_CHIP_ID_REG)
        print(f"Chip ID: 0x{chip_id:02x}")  # Should be 0xA0

if __name__ == "__main__":
    test_controller()
    test_imu()
    test_bno055_chip_id()