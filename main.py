import time

import config
from config import Positions
from src.nodes.controller import Controller

controller = Controller()

print('offsets', controller.offsets)
print('position', controller.positions)
time.sleep(2)



controller.set_target(Positions.ready)
print('ready', controller.move_to_target())
print(controller.pose.target_positions)
time.sleep(2)


"""
home {11: 491, 12: 500, 13: 375, 21: 508, 22: 500, 23: 625, 31: 508, 32: 500, 33: 625, 41: 491, 42: 500, 43: 375}
ready {11: 491, 12: 190, 13: 932, 21: 508, 22: 809, 23: 67, 31: 508, 32: 809, 33: 67, 41: 491, 42: 190, 43: 932}
crouch {11: 491, 12: 138, 13: 1000, 21: 508, 22: 861, 23: 0, 31: 508, 32: 861, 33: 0, 41: 491, 42: 138, 43: 1000}
"""
