import numpy as np
import serial
import config
from kinematics import Kinematics
from servo_controller import ServoController

"""
x = front-back
y = up
"""
k = Kinematics(config.coxa, config.femur, config.tibia)
try:
    controller = ServoController(serial.Serial('/dev/serial0'))
except:
    controller = None
    print("Robot will not move - couldn't open serial port.")



class Robot:
    def __init__(self):
        self.coxa = 50
        self.femur = 102
        self.tibia = 114

        self.positions = None
        self.offsets = None

        self.move_to(config.p_ready)

    def _offsets_from_positions(self, positions: np.ndarray):
        offsets = np.zeros((4,3))
        for i, pos in enumerate(positions):
            offsets[i] = np.degrees(k.ik(pos) - config.a_zero)

        return offsets

    def _move_command_from_offsets(self, offsets: np.ndarray):
        return dict(
            zip(
                config.servos.reshape(-1),
                ((offsets*config.flip*1000/240)+500).reshape(-1).astype(int)
            )
        )

    def move_to(self, positions: np.ndarray, millis = 500):
        offsets = self._offsets_from_positions(positions)
        cmd = self._move_command_from_offsets(offsets)

        if controller is not None:
            controller.move(cmd, millis/1000.0)

        self.offsets = offsets
        self.positions = positions

        return cmd

robot = Robot()
print('offsets', robot.offsets)
print('position', robot.positions)
print('command', robot.move_to(config.p_ready))