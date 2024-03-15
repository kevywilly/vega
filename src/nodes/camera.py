import cv2
import traitlets
from picamera2 import Picamera2

from config import CAMERA_MATRIX, DISTORTION_COEFFICIENTS
from src.nodes.node import Node


def _convert_color(frame):
    #return frame
    # XBGR8888  - SBGR10_CSI2P is what we get
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def _un_distort(frame):
    return cv2.undistort(frame, CAMERA_MATRIX, DISTORTION_COEFFICIENTS)


class Camera(Node):
    value = traitlets.Any()
    sensor_id = traitlets.Int(default_value=0)

    def __init__(self, **kwargs):
        super(Camera, self).__init__(**kwargs)
        self.frequency = 30
        self.cap = self._init_camera()
        self.log_camera_info()

        self.loaded()

    def log_camera_info(self):
        if self.cap:
            self.logger.debug('camera', self.cap.camera_properties)
            self.logger.debug('video', self.cap.video_configuration)
            self.logger.debug('still', self.cap.still_configuration)

    def _init_camera(self) -> Picamera2:
        cap = Picamera2()
        cap.start()
        frame = cap.capture_array()
        if frame is None:
            raise Exception("Could not initialize camera")
        else:
            self.value = frame
            return cap

    def _read(self, cap: Picamera2):

        try:
            frame = cap.capture_array()
            frame = _convert_color(frame)
            frame = cv2.flip(frame, 0)
            self.value = frame
        except:
            self.logger.warn(f"Can't receive frame from camera")

    def spinner(self):
        self._read(self.cap)

    def shutdown(self):
        try:
            self.logger.info("stopping camera")
            self.cap.stop()
            self.cap.close()
            self.logger.info("camera stopped")
        except:
            pass
