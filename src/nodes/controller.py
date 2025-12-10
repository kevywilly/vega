import atexit
import logging
import time

import numpy as np
import serial
from dataclasses import replace
from settings import settings
from src.interfaces.pose import Pose
from src.model.types import MoveTypes
from src.motion.gaits.gait import Gait
from src.motion.gaits.trot import Trot
from src.motion.gaits.turn import Turn
from src.motion.gaits.simplified_gait import (
    SimpleTrotWithLateral, SimpleSidestep
)
from src.motion.kinematics import QuadrupedKinematics
from src.motion.servo_controller import ServoController
from src.nodes.imu import IMUData
from src.nodes.node import Node
from src.signals import Topics

logger = logging.getLogger("VEGA")

_km = QuadrupedKinematics(
    settings.coxa_length,
    settings.femur_length,
    settings.tibia_length,
    settings.robot_width,
    settings.robot_length,
)

try:
    _sc = ServoController(serial.Serial(settings.serial_port))
except:  # noqa: E722
    _sc = None
    logger.debug("Robot will not move - couldn't open serial port.")

DEFAULT_MILLIS = 800
SERVO_MAX_ANGLE = np.radians(240)

# Pre-compute constants for servo position calculations (avoid repeated computation)
_SERVO_SCALE = 1000.0 / SERVO_MAX_ANGLE
_SERVO_IDS = np.array(settings.servo_ids)
_ANGLE_ZERO = settings.angle_zero
_ANGLE_FLIP = settings.angle_flip
# NOTE: position_offsets is NOT cached here - it changes at runtime via IMU leveling


def _angles_from_positions(positions: np.ndarray) -> np.ndarray:
    """Vectorized IK for all 4 legs - uses optimized numpy operations."""
    return _km.inverse_kinematics_vectorized(positions + settings.position_offsets)


def _positions_from_angles(angles: np.ndarray) -> np.ndarray:
    """Vectorized FK for all 4 legs."""
    positions = np.zeros((4, 3))
    for i in range(4):
        positions[i] = _km.forward_kinematics(angles[i])
    return positions - settings.position_offsets


def _servo_positions_from_angles(angles: np.ndarray) -> dict:
    """Optimized: vectorized servo position calculation."""
    # Vectorized calculation - no loops
    adjusted_angles = angles - _ANGLE_ZERO
    servo_values = (adjusted_angles * _ANGLE_FLIP * _SERVO_SCALE + 500).astype(np.int32).ravel()
    # Use pre-allocated dict pattern for speed
    return dict(zip(_SERVO_IDS, servo_values))


def _angles_from_servo_positions(servo_positions) -> np.ndarray:
    pos = _servo_positions_to_numpy(servo_positions)
    angles = (pos - 500) / (_ANGLE_FLIP * _SERVO_SCALE)
    return angles + _ANGLE_ZERO


def _servo_positions_to_numpy(servo_positions) -> np.ndarray:
    return np.array(list(servo_positions.values()), dtype=np.float32).reshape((4, 3))


def millis_or_default(millis):
    return DEFAULT_MILLIS if millis is None else millis


class Controller(Node):

    def __init__(self, **kwargs):
        super(Controller, self).__init__(**kwargs)
        self.pose = Pose()
        self.gait: Gait | None = None
        self.move_type: MoveTypes = MoveTypes.STOP
        self.moving: bool = False
        self._read_positions()
        self.set_targets(settings.position_ready)
        self.move_to(settings.position_ready, 400)
        self.imu_data: IMUData = IMUData()

        self.handle_subscriptions()

        atexit.register(self.shutdown)

    def shutdown(self):
        self.move_to(settings.position_sit, 500)
        time.sleep(0.2)

        if _sc:
            _sc.unload(settings.servo_ids)

    def handle_subscriptions(self):
        Topics.raw_imu.connect(self.on_raw_imu)

    def on_raw_imu(self, sender, payload: IMUData):
        # Use IMU data to adjust position offsets for leveling
        imu_data = payload
        self.imu_data = imu_data
        self.logger.debug(f"IMU Euler: {payload.euler}")

        return 
        roll = np.radians(imu_data.euler[0])
        pitch = np.radians(imu_data.euler[1])

        roll_matrix = np.array([
            [1, 0, 0],
            [0, np.cos(roll), -np.sin(roll)],
            [0, np.sin(roll), np.cos(roll)]
        ])

        pitch_matrix = np.array([
            [np.cos(pitch), 0, np.sin(pitch)],
            [0, 1, 0],
            [-np.sin(pitch), 0, np.cos(pitch)]
        ])

        self.roll_offsets = np.zeros((4, 3))
        self.pitch_offsets = np.zeros((4, 3))

        for i in range(4):
            leg_pos = self.pose.positions[i]
            rolled_pos = np.dot(roll_matrix, leg_pos)
            pitched_pos = np.dot(pitch_matrix, leg_pos)

            self.roll_offsets[i] = rolled_pos - leg_pos
            self.pitch_offsets[i] = pitched_pos - leg_pos

        settings.position_offsets = self.roll_offsets + self.pitch_offsets  

    def set_targets(self, positions: np.ndarray):
        self.pose.target_positions = positions
        self.pose.target_angles = _angles_from_positions(self.pose.target_positions)

    def set_target(self, index: int, positions: np.ndarray):
        self.pose.target_positions[index] = positions
        self.pose.target_angles = _angles_from_positions(self.pose.target_positions)

    def move_to_targets(self, millis=DEFAULT_MILLIS):
        return self.move_to(self.pose.target_positions, millis_or_default(millis))

    def move_to(self, positions: np.ndarray, millis=500):
        angles = _angles_from_positions(positions)
        cmd: dict = _servo_positions_from_angles(angles)

        if _sc is not None:
            _sc.move(cmd, millis_or_default(millis))

        self.pose.angles = angles
        self.pose.positions = positions
        self.pose.cmd = cmd
        logger.debug(self.pose)
        Topics.raw_pose.send("pose", payload=self.pose)
        return cmd

    def _read_positions(self):
        try:
            if _sc is not None:
                self.logger.debug(_sc.get_positions(settings.servo_ids))
                self.logger.debug(f"battery: {_sc.get_battery_voltage()}")
            # self.pose.servo_positions = _servo_positions_to_numpy(_sc.get_positions(SERVO_IDS))
            # self.pose.angles = _angles_from_servo_positions(self.pose.servo_positions)
            # self.pose.positions = _positions_from_angles(self.pose.angles)
        except:  # noqa: E722
            pass

    def ready(self, millis=100):
        self.move_to(settings.position_ready, millis)

    def stop(self):
        self.moving = False
        self.move_type = MoveTypes.STOP
        self.ready()
        return {"moving": self.moving, "move_type": self.move_type}
    
    def trot_in_place(self):
        gait = Trot(params=settings.trot_in_place_params)
        self.ready(200)
        self.logger.info("Trotting in place...")
        for i in range(int(gait.shape[0] * 2)):
            position = next(gait)
            self.move_to(position, 10)
        self.logger.info("Done trotting in place...")
        time.sleep(0.1)

    def process_move(self, move_type: MoveTypes):
        if move_type == MoveTypes.FORWARD:
            self.gait = SimpleTrotWithLateral(
                p0=settings.position_trot + settings.position_forward_offsets,
                params=settings.trot_params
            )
        elif move_type == MoveTypes.FORWARD_LT:
            self.gait = Turn(params=replace(settings.turn_params, turn_direction=1))
        elif move_type == MoveTypes.FORWARD_RT:
            self.gait = Turn(params=replace(settings.turn_params, turn_direction=-1))
        elif move_type == MoveTypes.BACKWARD:
            self.gait = SimpleTrotWithLateral(
                p0=settings.position_trot + settings.position_backward_offsets,
                params=settings.trot_reverse_params,
            )
        elif move_type == MoveTypes.BACKWARD_LT:
            self.gait = Turn(
                params=replace(settings.turn_params, turn_direction=-1, is_reversed=True)
            )
        elif move_type == MoveTypes.BACKWARD_RT:
            self.gait = Turn(params=replace(settings.turn_params, turn_direction=1, is_reversed=True))
        elif move_type == MoveTypes.LEFT:
            self.gait = SimpleSidestep(params=replace(settings.sidestep_params, is_reversed=True))
        elif move_type == MoveTypes.RIGHT:
            self.gait = SimpleSidestep(params=settings.sidestep_params)
        elif move_type == MoveTypes.TROT_IN_PLACE:
            self.gait = Trot(params=settings.trot_in_place_params)
        elif move_type == MoveTypes.STOP:
            return self.stop()

        self.move_type = move_type

        if self.move_type != MoveTypes.STOP:
            self.moving = True

        return {"moving": self.moving, "move_type": self.move_type}
    
    def set_pose(self, pose: str):
        v = pose.lower()

        p = None

        if v == "ready":
            p = settings.position_ready
        elif v == "sit":
            p = settings.position_sit
        elif v == "crouch":
            p = settings.position_crouch
        elif v == "walking":
            p = settings.position_walk
        elif v == "trotting":
            p = settings.position_trot
        else:
            return {"status": "error, unknown pose"}

        if self.moving:
            self.stop()
            time.sleep(0.5)

        self.set_targets(p)
        self.move_to_targets()

    @staticmethod
    def voltage():
        return 0.0

    def spinner(self):
        if self.moving and self.gait is not None:
            # Hot path: get next position and send to servos
            # next() is already optimized in Gait class
            position = next(self.gait)
            # time=0 means immediate move, no interpolation delay
            self.move_to(position, 0)
