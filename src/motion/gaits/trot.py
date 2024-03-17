import numpy as np


class Trotter:
    def __init__(self, mag=(50, 2, 50), num_steps=54):
        self.num_steps = num_steps
        self.x_mag, self.y_mag, self.z_mag = mag
        self.step_size = int(540 / num_steps)
        self.steps = self._generate_steps()

    def _generate_steps(self):
        x_steps = np.sin(np.radians(np.arange(0, 180, self.step_size / 2))) * self.x_mag
        x_steps2 = np.sin(np.radians(np.arange(180, 270, self.step_size / 2))) * self.x_mag
        x_steps = np.hstack([x_steps, x_steps2])

        y_steps = np.full((self.num_steps), self.y_mag)

        z_steps = np.sin(np.radians(np.arange(40,180,int(step_size*.8))))*self.z_mag
        z_steps = np.hstack([z_steps, np.zeros(int((180) * 2 / self.step_size))])

        steps = np.array(([x_steps, y_steps, z_steps]))
        return steps.reshape(-1, self.num_steps).transpose(1, 0).astype(int)

    def get_step(self, index):
        return self.steps[index]

    def step_generator(self):
        for i in range(self.num_steps):

            i2 = i + int(self.num_steps * 2 / 3)
            if i2 >= self.num_steps:
                i2 = 0

            l1_3 = self.get_step(i)
            l2_4 = self.get_step(i2)

            yield np.array([l1_3, l2_4, l1_3, l2_4])
