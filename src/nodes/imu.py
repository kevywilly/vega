import atexit
import numpy as np
from settings import settings
from src.nodes.node import Node
from src.signals import Topics
from dataclasses import dataclass, field

try:
    import adafruit_bno055
    import board
except:  # noqa: E722
    from src.mock import adafruit_bno055
    from src.mock.board import board


@dataclass
class IMUData:
    euler: np.ndarray = field(default_factory=lambda: np.zeros(3))
    acceleration: np.ndarray = field(default_factory=lambda: np.zeros(3))
    gyro: np.ndarray = field(default_factory=lambda: np.zeros(3))

    @property
    def heading(self) -> float:
        return self.euler[0]
    
    @property
    def roll(self) -> float:
        return self.euler[1]
    
    @property
    def pitch(self) -> float:
        return self.euler[2]
    
    @property
    def angular_vel(self) -> float:
        return self.gyro[2]
    
    @property
    def angular_accel(self) -> float:
        return self.acceleration[2]

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

    def __init__(self, **kwargs):
        super(IMU, self).__init__(**kwargs)
        self.sensor = adafruit_bno055.BNO055_I2C(board.I2C())
        self.sensor.mode = IMUMode.NDOF_MODE
        self.imu_data = IMUData()
        
        if settings.bno_axis_remap:
            self.sensor.axis_remap = settings.bno_axis_remap

        if settings.imu_gyro_offsets:
            self.sensor.offsets_gyroscope = tuple(settings.imu_gyro_offsets)

        if settings.imu_magnetic_offsets:
            self.sensor.offsets_magnetometer = tuple(settings.imu_magnetic_offsets)

        if settings.imu_acceleration_offsets:
            self.sensor.offsets_accelerometer = tuple(settings.imu_acceleration_offsets)

        self.read_measurements()

        atexit.register(self.shutdown)

    
    def read_measurements(self):
        try:
            # Only read euler (orientation) - most important for balance
            # Reading all 7 sensors takes 70-350ms and blocks GIL during gaits
            euler = np.round(np.array(self.sensor.euler),3)
            acceleration = np.round(np.array(self.sensor.acceleration),3)
            gyro = np.round(np.array(self.sensor.gyro),3)

            self.imu_data = IMUData(
                euler=euler,
                acceleration=acceleration,
                gyro=gyro
            )

            Topics.imu_raw.send(self.imu_data)

            # Uncomment these only if actively needed (slows down gaits)
            #
            #self.magnetic = np.round(np.array(self.sensor.magnetic),3)
            #self.quaternion = np.round(np.array(self.sensor.quaternion),4)
            #self.linear_acceleration = np.round(np.array(self.sensor.linear_acceleration),3)
            #self.gravity = np.round(np.array(self.sensor.gravity),3)

        except Exception as e:
            self.logger.warning(f"could not read imu {e.__str__()}")

    def spinner(self):
        self.read_measurements()
