import time
from typing import Optional

import numpy as np
import traitlets

from robolib.interfaces.msgs import Twist
from src.nodes.camera import Camera
from src.nodes.controller import Controller
from src.nodes.imu import IMU
from robolib.nodes.node import Node
from robolib.vision.image import Image, ImageUtils


class Measurement(traitlets.HasTraits):
    value = traitlets.Any(allow_none=True)


class CmdVel(traitlets.HasTraits):
    value = traitlets.Instance(Twist, allow_none=True)

    def numpy(self):
        if self.value is None:
            return np.zeros(3)
        else:
            return np.array([self.value.linear.x, self.value.linear.y, self.value.angular.z])


class Robot(Node):
    image = traitlets.Instance(Image)
    measurement = traitlets.Instance(Measurement)
    cmd_vel = traitlets.Instance(CmdVel)

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

        self._loaded()

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

    def print_stats(self):
        print("cmd", self.controller.pose.cmd)
        # print("targets", self.controller.pose.target_positions)
        # print("target_angles", self.controller.pose.target_angles)

    def spinner(self):
        pass
