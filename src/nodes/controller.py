import atexit

import numpy as np
import serial
from traitlets import HasTraits

import config
from config import Positions, Angles, Dims, servo_ids
from src.interfaces.pose import Pose
from src.motion.kinematics import Kinematics
from src.motion.servo_controller import ServoController

_km = Kinematics(Dims.coxa, Dims.femur, Dims.tibia)

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


"""
x = a * f * 1000 / 240 + 500
x - 500 = a * f * 1000 /240
a = (x - 500)*240/(f*1000)
"""


def _servo_positions_from_angles(angles: np.ndarray):
    adjusted_angles = angles - Angles.zero
    degrees = np.degrees(adjusted_angles)
    return dict(
        zip(
            config.servos.reshape(-1),
            ((degrees * config.flip * 1000 / SERVO_MAX_ANGLE) + 500).reshape(-1).astype(int)
        )
    )


def _angles_from_servo_positions(servo_positions):
    pos = _servo_positions_to_numpy(servo_positions)
    angles = (pos - 500) * SERVO_MAX_ANGLE / (config.flip * 1000)
    return angles + Angles.zero


def _servo_positions_to_numpy(servo_positions):
    return np.array(list(servo_positions.values())).reshape((4, -1))


class Controller(HasTraits):
    def __init__(self):
        self._sc = None
        self.positions = None
        self.offsets = None
        self.pose = Pose()
        self.read_positions()
        self.set_target(Positions.ready)
        self.move_to(self.pose.target_positions)

        atexit.register(self.shutdown)

        try:
            self._sc = ServoController(serial.Serial(config.serial_port))
        except:
            self._sc = None
            print(f"Robot will not move - couldn't open serial port.")

    def shutdown(self):
        self.move_to(Positions.crouch)
        if self._sc:
            self._sc.unload(servo_ids)

    def set_target(self, positions: np.ndarray):
        self.pose.target_positions = positions
        self.pose.target_angles = _angles_from_positions(positions)

    def move_to_target(self, millis=DEFAULT_MILLIS):
        return self.move_to(self.pose.target_positions)

    def move_to(self, positions: np.ndarray, millis=800):
        angles = _angles_from_positions(positions)
        cmd = _servo_positions_from_angles(angles)

        if self._sc is not None:
            self._sc.move(cmd, millis)

        self.pose.angles = angles
        self.pose.positions = positions

        return cmd

    def read_positions(self):
        if self._sc:
            self.pose.servo_positions = _servo_positions_to_numpy(self._sc.get_positions(servo_ids))
            self.pose.angles = _angles_from_servo_positions(self.pose.servo_positions)
            self.pose.positions = _positions_from_angles(self.pose.angles)
            return

        return np.zeros((4, 3))
