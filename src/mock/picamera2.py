from functools import cached_property

import cv2


class Picamera2:
    def __init__(self):
        self.running = False
        self.camera_properties = "Camera Properties ..."
        self.video_configuration = "Video Configuration ..."
        self.still_configuration = "Still Configuration ..."

    @cached_property
    def frame(self):
        return cv2.imread("src/mock/camera_image.jpg")

    def start(self):
        self.running = True

    def capture_array(self):
        return self.frame
        # return np.zeros((1640, 1232, 3))

    def stop(self):
        self.running = False

    def close(self):
        return
