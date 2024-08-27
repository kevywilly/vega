class Tilt:
    def __init__(self, pitch=0, yaw=0):
        self.pitch = int(pitch)
        self.yaw = int(yaw)

    def json(self):
        return {"pitch": self.pitch, "yaw": self.yaw, }