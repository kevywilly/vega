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
from src.motion.gaits.prowl import Prowl
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
        """Handle IMU data updates."""
        self.imu_data = payload
        self.logger.debug(f"IMU Euler: {payload.euler}")  

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

    def _get_gait_factory(self, move_type: MoveTypes):
        """Return a gait instance for the given move type."""
        factories = {
            MoveTypes.FORWARD: lambda: SimpleTrotWithLateral(
                p0=settings.position_trot + settings.position_forward_offsets,
                params=settings.trot_params
            ),
            MoveTypes.BACKWARD: lambda: SimpleTrotWithLateral(
                p0=settings.position_trot + settings.position_backward_offsets,
                params=settings.trot_reverse_params,
            ),
            MoveTypes.FORWARD_LT: lambda: Turn(params=replace(settings.turn_params, turn_direction=1)),
            MoveTypes.FORWARD_RT: lambda: Turn(params=replace(settings.turn_params, turn_direction=-1)),
            MoveTypes.BACKWARD_LT: lambda: Turn(params=replace(settings.turn_params, turn_direction=-1, is_reversed=True)),
            MoveTypes.BACKWARD_RT: lambda: Turn(params=replace(settings.turn_params, turn_direction=1, is_reversed=True)),
            MoveTypes.LEFT: lambda: SimpleSidestep(params=replace(settings.sidestep_params, is_reversed=True)),
            MoveTypes.RIGHT: lambda: SimpleSidestep(params=settings.sidestep_params),
            MoveTypes.TROT_IN_PLACE: lambda: Trot(params=settings.trot_in_place_params),
            MoveTypes.PROWL: lambda: Prowl(
                p0=settings.position_prowl,
                params=settings.prowl_params
            ),
            MoveTypes.PROWL_BACKWARD: lambda: Prowl(
                p0=settings.position_prowl,
                params=settings.prowl_reverse_params
            ),
        }
        factory = factories.get(move_type)
        return factory() if factory else None

    def process_move(self, move_type: MoveTypes):
        """Process a movement command and set up the appropriate gait."""
        if move_type == MoveTypes.STOP:
            return self.stop()

        gait = self._get_gait_factory(move_type)
        if gait:
            self.gait = gait
            self.move_type = move_type
            self.moving = True

        return {"moving": self.moving, "move_type": self.move_type}
    
    def set_pose(self, pose: str):
        """Set the robot to a named pose."""
        pose_map = {
            "ready": settings.position_ready,
            "sit": settings.position_sit,
            "crouch": settings.position_crouch,
            "walking": settings.position_walk,
            "trotting": settings.position_trot,
        }

        position = pose_map.get(pose.lower())
        if position is None:
            return {"status": "error, unknown pose"}

        if self.moving:
            self.stop()
            time.sleep(0.5)

        self.set_targets(position)
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
