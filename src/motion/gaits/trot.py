import numpy as np

class Trot:
    def __init__(self, mag_x=60, mag_y=20, mag_z=60, step_size=30):
        self.mag_x = mag_x
        self.mag_y = mag_y
        self.mag_z = mag_z
        step_size = step_size

        phase1_x = np.sin(np.radians(np.arange(0,90, step_size))) * self.mag_x      # 90
        phase2_x = np.sin(np.radians(np.arange(90,180, step_size))) * mag_x         # 90
        phase1_z = np.sin(np.radians(np.arange(0,180, step_size*2))) * self.mag_x   # 90
        phase2_z = np.zeros(int(90/step_size))                                      # 90



        self.x = np.hstack([phase1_x, phase2_x])
        self.y = np.full(self.x.size, -mag_y)
        self.z = np.hstack([phase1_z, phase2_z])

        phase3_x = np.cos(np.radians(np.arange(90,180,step_size/2))) * self.mag_x
        phase3_y = np.full(phase3_x.size,-mag_y)
        phase3_z = np.zeros(phase3_x.size)

        self.x2 = phase3_x
        self.y2 = phase3_y
        self.z2 = phase3_z

        self.steps = np.array([self.x, self.y, self.z])
        self.steps = -self.steps.reshape(-1, self.x.size).transpose(1, 0).astype(int)

        self.steps2 = np.array([self.x2, self.y2, self.z2])
        self.steps2 = -self.steps2.reshape(-1, self.x2.size).transpose(1, 0).astype(int)

    def step_generator(self):

        for i in range(self.x.size):

            l1_3 = self.steps[i]
            l2_4 = self.steps2[i]

            yield np.array([l1_3, l2_4, l1_3, l2_4])

        for i in range(self.x.size):

            l1_3 = self.steps2[i]
            l2_4 = self.steps[i]

            yield np.array([l1_3, l2_4, l1_3, l2_4])

class Trotter:
    def __init__(self, mag=(50, 4, 50), num_steps=54):
        self.num_steps = num_steps
        self.x_mag, self.y_mag, self.z_mag = mag
        self.step_size = int(180 / num_steps)
        self.steps = self._generate_steps()

    def _generate_steps_2(self):
        self.step_size = int(180 / self.num_steps)
        x_steps = np.sin(np.radians(np.arange(0, 180, self.step_size))) * self.x_mag
        #x_steps2 = np.sin(np.radians(np.arange(180, 270, self.step_size / 2))) * self.x_mag
        x_steps = -np.hstack([x_steps])

        y_steps = np.full((x_steps.size), self.y_mag)

        z_steps = -np.sin(np.radians(np.arange(0,180,int(self.step_size))))*self.z_mag
        #z_steps = np.hstack([z_steps, np.zeros(int((180) * 2 / self.step_size))])

        steps = np.array(([x_steps, y_steps, z_steps]))
        return steps.reshape(-1, x_steps.size).transpose(1, 0).astype(int)

    def _generate_steps(self):
        self.step_size = int(540 / self.num_steps)
        x_steps = np.sin(np.radians(np.arange(0, 180, self.step_size / 2))) * self.x_mag
        x_steps2 = np.sin(np.radians(np.arange(180, 270, self.step_size / 2))) * self.x_mag
        x_steps = -np.hstack([x_steps, x_steps2])

        y_steps = np.full((self.num_steps), self.y_mag)

        z_steps = -np.sin(np.radians(np.arange(0,180,int(self.step_size))))*self.z_mag
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

            yield np.array([l1_3, l1_3, l1_3, l1_3])
