import time
import logging
import numpy as np

from config import Positions
from src.nodes.controller import Controller
from src.nodes.robot import Robot

logger = logging.getLogger('VEGA')


robot = Robot()


time.sleep(1)

positions = [Positions.ready, Positions.crouch, Positions.ready]

for p in positions:
	robot.set_target(p)
	robot.move_to_target()
	robot.print_stats()
	time.sleep(2)


"""
command {11: 491, 12: 500, 13: 375, 21: 508, 22: 500, 23: 625, 31: 508, 32: 500, 33: 625, 41: 491, 42: 500, 43: 375}
ready {11: 491, 12: 315, 13: 720, 21: 508, 22: 684, 23: 279, 31: 508, 32: 684, 33: 279, 41: 491, 42: 315, 43: 720}
crouch {11: 491, 12: 166, 13: 966, 21: 508, 22: 833, 23: 33, 31: 508, 32: 833, 33: 33, 41: 491, 42: 166, 43: 966}
"""
