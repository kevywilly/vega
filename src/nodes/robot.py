import time
from typing import Optional, Dict

import numpy as np
import traitlets

from config import POSITIONS, trot_params, sidestep_params, turn_params
from src.interfaces.msgs import Twist
from src.motion.gaits.gait import Gait
from src.motion.gaits.sidestep import Sidestep
from src.motion.gaits.trot import Trot
from src.motion.gaits.trot2 import Trot2
from src.motion.gaits.turn import Turn
from src.nodes.camera import Camera
from src.nodes.controller import Controller
from src.nodes.imu import IMU
from src.nodes.node import Node
from src.vision.image import Image, ImageUtils
from src.interfaces.pose import Pose


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
            return np.array([self.value.linear.x, self.value.linear.y, self.value.angular.z])


class DriveCmd(traitlets.HasTraits):
    stride = traitlets.Int(allow_none=True)


class Robot(Node):
    image = traitlets.Instance(Image)
    measurement = traitlets.Instance(Measurement)
    cmd_vel = traitlets.Instance(CmdVel)
    walking = traitlets.Bool(allow_none=True, default=False)
    walking_dir = traitlets.Unicode(allow_none=True)
    joy_id = traitlets.Int(allow_none=True)
    gait = traitlets.Any(Gait, allow_none=True)
    stats = traitlets.Instance(PoseStatus, allow_none=True)

    def __init__(self, **kwargs):
        super(Robot, self).__init__(**kwargs)

        # initialize objects
        self.session_id = str(int(time.time()))

        self.image = Image()
        self.measurement = Measurement()
        self.cmd_vel = CmdVel()
        self.pose_status = PoseStatus()
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

        self.loaded()

    def _start_nodes(self):
        self.imu.spin()
        self.controller.spin()
        if self.camera:
            self.camera.spin()

    def _setup_subscriptions(self):
        if self.camera:
            traitlets.dlink((self.camera, 'value'), (self.image, 'value'), transform=ImageUtils.bgr8_to_jpeg)
            if self.controller:
                traitlets.dlink((self.camera, 'value'), (self.controller, 'camera_image'))
        if self.controller:
            traitlets.dlink((self.controller, 'cmd_vel'), (self.cmd_vel, 'value'))
            traitlets.dlink((self.imu, 'euler'), (self.controller, 'euler'))
            traitlets.dlink((self.controller, 'pose'), (self.pose_status, 'pose'))

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
                        b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + self.get_image() + b'\r\n'
                )  # concat frame one by one and show result
            except Exception:
                pass

    def stop(self):
        self.walking = False
        self.walking_dir = 'C'
        self.joy_id = 0
        time.sleep(0.1)
        self.controller.move_to(POSITIONS.READY)
        time.sleep(0.1)

    def spinner(self):
        if self.walking and self.gait is not None:
            position = next(self.gait)
            self.controller.move_to(position, 10)

    def process_joy(self, data: Dict):
        dir = data.get("dir")
        x = int(data.get("x", "0"))
        y = int(data.get("y", "0"))
        jid = int(data.get("id", "0"))

        def response():
            return {
                "walking": self.walking,
                "dir": self.walking_dir,
                "joy_id": self.joy_id,
                "gait": self.gait.__class__.__name__ if self.gait else None
            }

        if dir == 'C':
            self.stop()
            return response()
        if self.walking_dir == dir and self.joy_id == jid:
            return response()

        if dir == 'N':
            self.gait = Trot(**trot_params)
        elif dir == "S":
            self.gait = Trot2(p0=POSITIONS.READY_REVERSE,  **trot_params, reversed=True)
        elif dir == "E" and jid == 1:
            self.gait = Sidestep(**sidestep_params)
        elif dir == "E" and jid == 2:
            self.gait = Turn(**turn_params)
        elif dir == "W" and jid == 1:
            self.gait = Sidestep(**sidestep_params, reversed=True)
        elif dir == "W" and jid == 2:
            self.gait = Turn(**turn_params, reversed=True)

        self.walking_dir = dir
        self.walking = True
        self.joy_id = jid

        return response()
