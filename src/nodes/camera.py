import cv2
import traitlets

from src.vision.sensors import CameraSensor
from config import DEFAULT_SENSOR_MODE, CAMERA_MATRIX, DISTORTION_COEFFICIENTS
from src.nodes.node import Node


def _convert_color(frame):
    return cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_I420)


def _un_distort(frame):
    return cv2.undistort(frame, CAMERA_MATRIX, DISTORTION_COEFFICIENTS)


class Camera(Node):
    value = traitlets.Any()
    sensor_id = traitlets.Int(default_value=0)

    def __init__(self, **kwargs):
        super(Camera, self).__init__(**kwargs)
        self.sensor_mode = CameraSensor.mode(DEFAULT_SENSOR_MODE)
        self.frequency = self.sensor_mode.framerate
        self.cap = self._init_camera()

        self.loaded()

    def _init_camera(self) -> cv2.VideoCapture:
        cap = cv2.VideoCapture(self.sensor_mode.to_nvargus_string(self.sensor_id))
        ret, frame = cap.read()
        if not ret:
            raise Exception("Could not initialize camera")
        else:
            self.value = frame
            return cap

    def _read(self, cap: cv2.VideoCapture):

        if not cap.isOpened():
            return

        ret, frame = cap.read()

        if not ret:
            self.logger.warn(f"Can't receive frame for cap{self.sensor_id}")
        else:
            frame = _convert_color(frame)
            frame = _un_distort(frame)
            self.value = frame
            """
            try:
                cv2.namedWindow("felix", cv2.WINDOW_NORMAL)
                i2 = cv2.resize(frame, (300,300), cv2.INTER_LINEAR)
                cv2.imshow("felix", i2)
                cv2.waitKey(0)
            except Exception as ex:
                raise ex
                pass
            """

    def spinner(self):
        self._read(self.cap)

    def shutdown(self):
        try:
            cv2.destroyAllWindows()
        except:
            pass
        if self.cap:
            self.cap.release()
