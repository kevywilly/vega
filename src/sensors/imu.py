import numpy as np
import traitlets

ZEROS = np.zeros((3))


class Imu(traitlets.HasTraits):
    accelerometer = traitlets.Any()
    magnometer = traitlets.Any()
    gyroscope = traitlets.Any()
    attitude = traitlets.Any()

    def __init__(self, *args, **kwargs):
        super(Imu, self).__init__(*args, **kwargs)
        self.accelerometer = ZEROS
        self.magnometer = ZEROS
        self.gyroscope = ZEROS
        self.attitude_data = ZEROS

    def read(self):
        pass


"""

"""