import time

import numpy as np
import traitlets

from src.interfaces.msgs import Twist
from src.nodes.camera import Camera
from src.nodes.controller import Controller
from src.nodes.imu import IMU
from src.nodes.node import Node
from src.vision.image import Image, ImageUtils


class Measurement(traitlets.HasTraits):
    value = traitlets.Any(allow_none=True)


class CmdVel(traitlets.HasTraits):
    value = traitlets.Instance(Twist, allow_none=True)

    def numpy(self):
        if self.value is None:
            return np.zeros((3))
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
            self.camera: Camera = Camera()
        except:
            self.camera = None

        self.imu = IMU()
        self.controller: Controller = Controller(frequency=30)

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
            traitlets.dlink((self.camera, 'value'), (self.controller, 'camera_image'))
        traitlets.dlink((self.controller, 'cmd_vel'), (self.cmd_vel, 'value'))
        # traitlets.dlink((self.camera, 'value'), (self._video_viewer, 'camera_image'))

    def shutdown(self):
        if self.camera:
            self.camera.unobserve_all()
        self.controller.unobserve_all()

    def get_image(self):
        return self.image.value

    def set_cmd_vel(self, msg: Twist):
        self.controller.cmd_vel = msg

    def set_target(self, positions: np.ndarray):
        return self.controller.set_target(positions)

    def move_to_target(self, millis=None):
        return self.controller.move_to_target(millis)

    def move_to_position(self, positions: np.ndarray, millis=None):
        return self.controller.move_to(positions, millis)

    def get_stream(self):
        while True:
            # ret, buffer = cv2.imencode('.jpg', frame)
            try:
                yield (
                        b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + self.get_image() + b'\r\n'
                )  # concat frame one by one and show result
            except Exception as ex:
                pass

    def print_stats(self):
        print("cmd", self.controller.pose.cmd)
        # print("targets", self.controller.pose.target_positions)
        # print("target_angles", self.controller.pose.target_angles)

    def spinner(self):
        pass
