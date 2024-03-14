

from picamera2 import Picamera2, Preview
picam2 = Picamera2()
#picam2.start_preview(Preview.NULL)
#picam2.start_and_capture_file("test.jpg")
picam2.start()
picam2.capture_array()