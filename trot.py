from src.nodes.robot import Robot 
from src.motion.gaits.trot import Trot
from config import Positions
robot = Robot()

import time
target = Positions.crouch
num_steps = 54
import numpy as np



def demo():
    positions = [Positions.ready, Positions.crouch, Positions.ready]
    print(positions)
    for p in positions:
        robot.set_targets(p)
        robot.move_to_targets()
        robot.print_stats()
        time.sleep(2)


def walk():
    trotter = Trot(mag_x=55, mag_y=0, mag_z=65, step_size=15)
    robot.controller.move_to(Positions.ready2)
    time.sleep(0.5)
    while 1:
        for position in trotter.step_generator(reverse=False):
            position = position + Positions.ready2
            robot.controller.move_to(position, 50)


def crouch_walk():
    trotter = Trot(mag_x=50, mag_y=0, mag_z=50, step_size=10)
    robot.controller.move_to(Positions.crouch)
    time.sleep(0.5)
    while 1:
        for position in trotter.step_generator(reverse=False):
            position = position + Positions.ready
            robot.controller.move_to(position, 70)


walk()
