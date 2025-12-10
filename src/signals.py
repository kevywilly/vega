from blinker import signal

class Topics:
    raw_imu = signal('raw_imu')
    raw_pose = signal('pose_raw')
    raw_image = signal('raw_image')
    