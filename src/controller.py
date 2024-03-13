import numpy as np
import serial
import config
from kinematics import Kinematics
from servo_controller import ServoController
import time

class Controller:

    def __init__(self, coxa, femur, tibia):
        self.km = Kinematics(config.coxa, config.femur, config.tibia)

        try:
            self._sc = ServoController(serial.Serial('/dev/serial0'))
        except:
            self._sc = None
            print("Robot will not move - couldn't open serial port.")

    def _offsets_from_positions(self, positions: np.ndarray):
        offsets = np.zeros((4,3))
        for i, pos in enumerate(positions):
            offsets[i] = np.degrees(self.km.ik(pos) - config.a_zero)

        return offsets

    def _move_command_from_offsets(self, offsets: np.ndarray):
        return dict(
            zip(
                config.servos.reshape(-1),
                ((offsets*config.flip*1000/240)+500).reshape(-1).astype(int)
            )
        )

    def move_to(self, positions: np.ndarray, millis = 800):
        offsets = self._offsets_from_positions(positions)
        cmd = self._move_command_from_offsets(offsets)

        if self._sc is not None:
            self._sc.move(cmd, millis)

        self.offsets = offsets
        self.positions = positions

        return cmd