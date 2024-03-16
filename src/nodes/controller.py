import atexit

import numpy as np
import serial
import traitlets

import config
from config import Positions, Angles, Dims, SERVO_IDS, FLIP, POSITION_OFFSETS
from src.interfaces.msgs import Twist, Odometry
from src.interfaces.pose import Pose
from src.motion.kinematics import Kinematics
from src.motion.servo_controller import ServoController
from src.nodes.node import Node
import logging
logger = logging.getLogger('VEGA')

_km = Kinematics(Dims.coxa, Dims.femur, Dims.tibia)

try:
    _sc = ServoController(serial.Serial(config.serial_port))
except:
    _sc = None
    logger.debug(f"Robot will not move - couldn't open serial port.")
    
DEFAULT_MILLIS = 800
SERVO_MAX_ANGLE = np.radians(240)


def _angles_from_positions(positions: np.ndarray):
    angles = np.zeros((4, 3))
    for i, pos in enumerate(positions):
        angles[i] = _km.ik(pos)

    return angles


def _positions_from_angles(angles: np.ndarray):
    positions = np.zeros((4, 3))
    for i, ang in enumerate(angles):
        positions[i] = _km.fk(ang)

    return positions


def _servo_positions_from_angles(angles: np.ndarray):
    adjusted_angles = angles - Angles.zero
    return dict(
        zip(
            config.SERVOS.reshape(-1),
            ((adjusted_angles * FLIP * 1000 / SERVO_MAX_ANGLE) + 500).reshape(-1).astype(int)
        )
    )


def _angles_from_servo_positions(servo_positions):
    pos = _servo_positions_to_numpy(servo_positions)
    angles = (pos - 500) * SERVO_MAX_ANGLE / (FLIP * 1000)
    return angles + Angles.zero


def _servo_positions_to_numpy(servo_positions):
    return np.array(list(servo_positions.values())).reshape((4, -1))


def millis_or_default(millis):
    return DEFAULT_MILLIS if millis is None else millis


class Controller(Node):
    cmd_vel = traitlets.Instance(Twist, allow_none=True)
    nav_target = traitlets.Instance(Odometry, allow_none=True)
    publish_frequency_hz = traitlets.Int(default_value=10, config=True)
    camera_image = traitlets.Any(allow_none=True)
    euler = traitlets.Any(allow_none=True)

    attitude_data = traitlets.Any()
    magnometer_data = traitlets.Any()
    gyroscope_data = traitlets.Any()
    accelerometer_data = traitlets.Any()
    motion_data = traitlets.Any()

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self.positions = None
        self.offsets = None
        self.pose = Pose()
        self.cmd = None
        self._read_positions()
        self.set_targets(Positions.ready)
        self.move_to(self.pose.target_positions)

        atexit.register(self.shutdown)


    def _apply_cmd_vel(self, cmd: Twist):
        pass

    @traitlets.observe('cmd_vel')
    def _cmd_val_change(self, change):
        self._apply_cmd_vel(change.new)

    def shutdown(self):
        self.move_to(Positions.crouch)
        if _sc:
            _sc.unload(SERVO_IDS)

    def set_targets(self, positions: np.ndarray):
        self.pose.target_positions = positions
        self.pose.target_angles = _angles_from_positions(self.pose.target_positions)

    def set_target(self, index: int, positions: np.ndarray):
        self.pose.target_positions[index] = positions
        self.pose.target_angles = _angles_from_positions(self.pose.target_positions)

    def move_to_targets(self, millis=DEFAULT_MILLIS):
        return self.move_to(self.pose.target_positions, millis_or_default(millis))

    def move_to(self, positions: np.ndarray, millis=800):
        angles = _angles_from_positions(positions+POSITION_OFFSETS)
        cmd = _servo_positions_from_angles(angles)

        if _sc is not None:
            _sc.move(cmd, millis_or_default(millis))

        self.pose.angles = angles
        self.pose.positions = positions
        self.pose.cmd = cmd
        return cmd

    def _read_positions(self):
        try:
            self.logger.info(_sc.get_positions(SERVO_IDS))
            self.logger.info(f"battery: {_sc.get_battery_voltage()}")
            #self.pose.servo_positions = _servo_positions_to_numpy(_sc.get_positions(SERVO_IDS))
            #self.pose.angles = _angles_from_servo_positions(self.pose.servo_positions)
            #self.pose.positions = _positions_from_angles(self.pose.angles)
        except:
            pass

    @traitlets.observe('euler')
    def _on_euler(self, change):
        self.logger.info(f'euler: {self.euler}')


    def spinner(self):
        pass
