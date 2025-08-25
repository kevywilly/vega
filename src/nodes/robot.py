from dataclasses import dataclass, field
import time
from typing import Optional

import numpy as np
import traitlets

from settings import settings
from src.interfaces.msgs import Twist
from src.interfaces.pose import Pose
from src.model.types import MoveTypes
from src.motion.gaits.gait import Gait
from src.motion.gaits.sidestep import Sidestep
from src.motion.gaits.simplified_gait import (
    SimpleTrotWithLateral, SimpleSidestep, SimpleTurn
)
from src.motion.gaits.trot import Trot
from src.motion.gaits.turn import Turn

# from src.motion.gaits.turning_gait import TurningGait as Turn
from src.nodes.camera import Camera
from src.nodes.controller import Controller
from src.nodes.imu import IMU
from src.nodes.node import Node
from src.vision.image import Image, ImageUtils


def _array_to_dict(ar, label: str = "Leg"):
    return {
        f"{label} {i}": {"x": float(x), "y": float(y), "z": z}
        for i, (x, y, z) in enumerate(ar)
    }


class Measurement(traitlets.HasTraits):
    value = traitlets.Any(allow_none=True)


class PoseStatus(traitlets.HasTraits):
    pose = traitlets.Instance(Pose, allow_none=True)


class CmdVel(traitlets.HasTraits):
    value = traitlets.Instance(Twist, allow_none=True)

    def numpy(self):
        if self.value is None:
            return np.zeros(3)
        else:
            return np.array(
                [self.value.linear.x, self.value.linear.y, self.value.angular.z]
            )


class DriveCmd(traitlets.HasTraits):
    stride = traitlets.Int(allow_none=True)


@dataclass
class RobotData:
    heading: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    angular_vel: float = 0.0
    angular_accel: float = 0.0
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
    image = traitlets.Instance(Image)
    measurement = traitlets.Instance(Measurement)
    cmd_vel = traitlets.Instance(CmdVel)
    moving = traitlets.Bool(allow_none=True, default=False)
    move_type = traitlets.Unicode(allow_none=True, default=MoveTypes.STOP)
    joy_id = traitlets.Int(allow_none=True)
    gait = traitlets.Any(Gait, allow_none=True)
    yaw_offsets = traitlets.Any(default_value=np.zeros((4, 3)))
    pitch_offsets = traitlets.Any(default_value=np.zeros((4, 3)))

    def __init__(self, **kwargs):
        super(Robot, self).__init__(**kwargs)

        # initialize objects
        self.session_id = str(int(time.time()))

        self.image = Image()
        self.measurement = Measurement()
        self.cmd_vel = CmdVel()
        self.cmd_zero = True

        # initialize nodes
        try:
            self.camera: Optional[Camera] = Camera()
        except Exception as ex:
            self.logger.error(ex.__str__())
            self.camera = None

        self.controller: Controller = Controller(frequency=30)

        self.imu = IMU()

        self._start_nodes()
        self._setup_subscriptions()
        time.sleep(0.2)

        self.auto_level()

        self.loaded()

    def _start_nodes(self):
        self.imu.spin()
        self.controller.spin()
        if self.camera:
            self.camera.spin()

    def _setup_subscriptions(self):
        if self.camera:
            traitlets.dlink(
                (self.camera, "value"),
                (self.image, "value"),
                transform=ImageUtils.bgr8_to_jpeg,
            )
            if self.controller:
                traitlets.dlink(
                    (self.camera, "value"), (self.controller, "camera_image")
                )
        if self.controller:
            traitlets.dlink((self.controller, "cmd_vel"), (self.cmd_vel, "value"))
            traitlets.dlink((self.imu, "euler"), (self.controller, "euler"))

        # traitlets.dlink((self.camera, 'value'), (self._video_viewer, 'camera_image'))

    def get_image(self):
        return self.image.value

    def get_imu(self):
        return self.imu.euler

    def set_cmd_vel(self, msg: Twist):
        self.controller.cmd_vel = msg

    def set_targets(self, positions: np.ndarray):
        return self.controller.set_targets(positions)

    def move_to_targets(self, millis=None):
        return self.controller.move_to_targets(millis)

    def get_stream(self):
        while True:
            # ret, buffer = cv2.imencode('.jpg', frame)
            try:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + self.get_image() + b"\r\n"
                )  # concat frame one by one and show result
            except Exception:
                pass

    def stop(self):
        self.moving = False
        self.move_type = MoveTypes.STOP
        self.ready()
        return {"moving": self.moving, "move_type": self.move_type}

    def process_move(self, move_type: MoveTypes):
        if move_type == MoveTypes.FORWARD:
            self.gait = SimpleTrotWithLateral(
                p0=settings.position_trot + settings.position_forward_offsets,
                **settings.trot_params      # Step size for smoothness
            )
            # self.gait = Trot(
            #    p0=settings.position_ready + settings.position_forward_offsets,
            #    **settings.trot_params,
            #)
        elif move_type == MoveTypes.FORWARD_LT:
            self.gait = Turn(**settings.turn_params, turn_direction=1)
        elif move_type == MoveTypes.FORWARD_RT:
            self.gait = Turn(**settings.turn_params, turn_direction=-1)
        elif move_type == MoveTypes.BACKWARD:
            self.gait = SimpleTrotWithLateral(
                p0=settings.position_trot + settings.position_backward_offsets,
                **settings.trot_reverse_params,
            )
        elif move_type == MoveTypes.BACKWARD_LT:
            self.gait = Turn(
                **settings.turn_params, turn_direction=-1, is_reversed=True
            )
        elif move_type == MoveTypes.BACKWARD_RT:
            self.gait = Turn(**settings.turn_params, turn_direction=1, is_reversed=True)
        elif move_type == MoveTypes.LEFT:
            self.gait = SimpleSidestep(**settings.sidestep_params, is_reversed=True)
        elif move_type == MoveTypes.RIGHT:
            self.gait = SimpleSidestep(**settings.sidestep_params)
        elif move_type == MoveTypes.TROT_IN_PLACE:
            self.gait = Trot(**settings.trot_in_place_params)
        elif move_type == MoveTypes.STOP:
            return self.stop()

        self.move_type = move_type

        if self.move_type != MoveTypes.STOP:
            self.moving = True

        return {"moving": self.moving, "move_type": self.move_type}

    def demo(self):
        positions = [
            settings.position_ready,
            settings.position_crouch,
            settings.position_ready,
            settings.position_sit,
        ]

        for p in positions:
            self.set_targets(p)
            self.move_to_targets()
            time.sleep(2)

    def trot_in_place(self):
        gait = Trot(**settings.trot_in_place_params)
        self.ready(200)
        self.logger.info("Trotting in place...")
        for i in range(int(gait.shape[0] * 2)):
            position = next(gait)
            self.controller.move_to(position, 10)
        self.logger.info("Done trotting in place...")
        time.sleep(0.1)

    def auto_level(self):
        if settings.auto_level:
            for i in range(3):
                self.logger.info(f"*** Leveling pass {i} ***")
                if self.level():
                    return

    def level(self) -> bool:
        self.logger.info("**** Performing Level Calibration ***")
        try:
            self.trot_in_place()
            self.ready(100)
            time.sleep(0.2)
            pitch_array = np.array([1, -1, -1, 1]).astype(int)
            yaw_array = np.array([-1, -1, 1, 1]).astype(int)
            zeros = np.zeros(4)
            roll, pitch, yaw = self.imu.euler

            for i in range(10):
                if abs(pitch) > settings.pitch_threshold:
                    pitch_offset = pitch_array if pitch >= 0 else -pitch_array
                else:
                    pitch_offset = zeros

                if abs(yaw) > settings.yaw_threshold:
                    yaw_offset = yaw_array if (yaw >= 0) else -yaw_array
                else:
                    yaw_offset = zeros

                settings.position_offsets[:, 2] += (pitch_offset + yaw_offset).astype(
                    int
                )
                self.logger.info(
                    f"pitch: {pitch} yaw: {yaw} setting offset => {settings.position_offsets.flatten().tolist()}"
                )
                self.ready(10)

                time.sleep(0.3)

                roll, pitch, yaw = self.imu.euler

                if (
                    abs(pitch) <= settings.pitch_threshold
                    and abs(yaw) <= settings.yaw_threshold
                ):
                    self.logger.info(
                        f"leveling succeeded...pitch...{pitch} yaw...{yaw}"
                    )
                    return True

        except Exception as ex:
            self.ready(200)
            self.logger.error(ex)

        self.logger.info(f"leveling failed...pitch...{pitch} yaw...{yaw}")
        settings.reset_offsets()
        self.ready(200)
        return False

    def ready(self, millis=200):
        self.controller.move_to(settings.position_ready, millis)

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
        else:
            return {"status": "error, unknown pose"}

        if self.moving:
            self.stop()
            time.sleep(0.5)

        self.set_targets(p)
        self.move_to_targets()

    @property
    def stats(self) -> dict:
        euler = dict(zip(["heading", "pitch", "yaw"], self.imu.euler))
        angular_velocity = dict(zip(["x", "y", "z"], self.imu.gyro))
        angular_acceleration = dict(zip(["x", "y", "z"], self.imu.acceleration))
        pose = self.controller.pose
        return {
            "euler": euler,
            "angular_velocity": angular_velocity,
            "angular_acceleration": angular_acceleration,
            "angles": pose.angles_in_degrees.tolist(),
            "positions": pose.positions.astype(int).tolist(),
            "offsets": settings.position_offsets.astype(int).tolist(),
            "tilt": settings.tilt.json(),
            "height": pose.height,
            "height_pct": pose.height_pct,
        }

    @property
    def data(self) -> RobotData:
        pose = self.controller.pose
        return RobotData(
            heading=self.imu.euler[0],
            pitch=self.imu.euler[1],
            yaw=self.imu.euler[2],
            angular_vel=self.imu.gyro[2],
            angular_accel=self.imu.acceleration[2],
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
            moving=self.moving,
            move_type=self.move_type,
        )

    def spinner(self):
        if self.moving and self.gait is not None:
            position = next(self.gait)
            self.controller.move_to(position, 10)
