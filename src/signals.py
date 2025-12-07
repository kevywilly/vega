from blinker import signal

class Topics:
    imu_raw = signal('imu_raw')
    pose_raw = signal('pose_raw')
    