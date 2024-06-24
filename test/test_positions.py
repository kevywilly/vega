import config as config
from src.nodes.robot import Robot
import numpy as np


def test_pback():
    robot = Robot()
    robot.spin()
    assert robot.controller.pose.cmd_as_array[0][1] == 309
    p = config.POSITIONS.READY_REVERSE
    p2 = config.POSITIONS.READY_REVERSE * config.POSITION_FLIP

    robot.set_targets(p)
    robot.move_to_targets()
    v1 = robot.controller.pose.cmd_as_array[0][1]
    assert robot.controller.pose.cmd_as_array[0][1] == 344

    assert True


def test_p0():
    robot = Robot()
    robot.spin()
    assert robot.controller.pose.cmd_as_array[0][1] == 309
    ready = config.POSITIONS.READY

    config.POSITIONS.OFFSETS = np.array([[15,0,0],[15,0,0],[15,0,0],[15,0,0]])
    robot.set_targets(ready)
    robot.move_to_targets()
    v1 = robot.controller.pose.cmd_as_array[0][1]
    assert robot.controller.pose.cmd_as_array[0][1] == 344

    config.POSITIONS.OFFSETS = np.array([[-15, 0, 0], [-15, 0, 0], [-15, 0, 0], [-15, 0, 0]])
    robot.set_targets(ready)
    robot.move_to_targets()
    assert robot.controller.pose.cmd_as_array[0][1] == 278

    assert True

