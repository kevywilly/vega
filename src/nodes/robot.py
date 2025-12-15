from dataclasses import dataclass, field
import time

import numpy as np

from settings import settings
from src.interfaces.pose import Pose
from src.model.types import MoveTypes
from src.nodes.controller import Controller
from src.nodes.imu import IMU, IMUData
from src.nodes.node import Node


def _array_to_dict(ar, label: str = "Leg"):
    return {
        f"{label} {i}": {"x": float(x), "y": float(y), "z": z}
        for i, (x, y, z) in enumerate(ar)
    }


@dataclass
class RobotData:
    imu: IMUData = IMUData()
    positions: dict = field(default_factory=lambda: _array_to_dict(Pose().positions))
    angles: dict = field(
        default_factory=lambda: _array_to_dict(Pose().angles_in_degrees)
    )
    offsets: dict = field(
        default_factory=lambda: _array_to_dict(settings.default_position_offsets)
    )
    moving: bool = False
    move_type: MoveTypes = MoveTypes.STOP


class Robot(Node):

    def __init__(self, controller: Controller, imu: IMU, **kwargs):
        super(Robot, self).__init__(**kwargs)

        # initialize objects
        self.session_id = str(int(time.time()))
        self.image = None
        self.roll_offsets: np.ndarray = np.zeros((4, 3))
        self.pitch_offsets: np.ndarray = np.zeros((4, 3))
        self.controller = controller
        self.imu = imu

        self.loaded()

    def stop(self):
        self.controller.stop()

    def demo(self):
        positions = [
            settings.position_ready,
            settings.position_crouch,
            settings.position_ready,
            settings.position_sit,
        ]

        for p in positions:
            self.controller.set_targets(p)
            self.controller.move_to_targets()
            time.sleep(2)

    def trot_in_place(self):
        self.controller.trot_in_place()

    def auto_level(self):
        if settings.auto_level:
            for i in range(3):
                self.logger.info(f"*** Leveling pass {i} ***")
                if self.level():
                    return

    def ready(self, millis=200):
        self.controller.ready(millis)

    def set_pose(self, pose: str):
        self.controller.set_pose(pose)

    @property
    def data(self) -> RobotData:
        pose = self.controller.pose
        return RobotData(
            imu=self.imu.imu_data,
            positions={
                f"Leg {i}": {"x": pos[0], "y": pos[1], "z": pos[2]}
                for i, pos in enumerate(pose.positions)
            },
            angles={
                f"Leg {i}": {"coxa": angle[0], "femur": angle[1], "tibia": angle[2]}
                for i, angle in enumerate(pose.angles_in_degrees)
            },
            offsets={
                f"Leg {i}": {"x": offset[0], "y": offset[1], "z": offset[2]}
                for i, offset in enumerate(settings.position_offsets)
            },
            moving=self.controller.moving,
            move_type=self.controller.move_type
        )

    def spinner(self):
        """Optimized main control loop - minimizes overhead in hot path."""
        pass

    def level(self) -> bool:
        """Perform automatic leveling calibration using IMU feedback."""
        self.logger.info("**** Performing Level Calibration ***")
        try:
            self.trot_in_place()
            self.ready(100)
            time.sleep(0.2)

            # Offset adjustment arrays for roll correction
            roll_array = np.array([1, -1, -1, 1])

            for _ in range(10):
                _, roll, pitch = self.imu.sensor.euler
                self.logger.debug(f"roll: {roll:.2f}, pitch: {pitch:.2f}")

                if roll is not None and abs(roll) > settings.roll_threshold:
                    offset = roll_array if roll >= 0 else -roll_array
                    settings.position_offsets[:, 2] += offset.astype(int)
                    self.logger.debug(f"offset => {settings.position_offsets[:, 2].tolist()}")
                else:
                    self.logger.info(f"leveling succeeded! roll: {roll:.2f}, pitch: {pitch:.2f}")
                    return True

                self.ready(10)
                time.sleep(0.3)

        except Exception as ex:
            self.ready(200)
            self.logger.error(ex)

        self.logger.info(f"leveling failed... roll: {roll:.2f}, pitch: {pitch:.2f}")
        settings.reset_offsets()
        self.ready(200)
        return False