import time

import config
from config import Positions
from src.nodes.controller import Controller

controller = Controller()

print('offsets', controller.offsets)
print('position', controller.positions)
time.sleep(2)

while 1:
    controller.set_target(Positions.home)
    print('ready', controller.move_to_target())
    time.sleep(2)
    controller.set_target(Positions.ready)
    print('ready', controller.move_to_target())
    time.sleep(2)
    controller.set_target(Positions.crouch)
    print('crouch', controller.move_to_target())
    time.sleep(2)
    controller.set_target(Positions.home)
    print('home', controller.move_to_target())
    time.sleep(2)
    break
