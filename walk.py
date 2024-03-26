from src.motion.gaits.sideways import Sideways
from src.motion.gaits.turn import Turn
from src.nodes.robot import Robot
from src.motion.gaits.trot import Trot, BasicTrot
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


def trot():
    gait = Trot(p0 = Positions.ready2, mag_x=60, mag_y=0, mag_z=60, step_size=15)
    robot.controller.move_to(Positions.ready2)
    time.sleep(0.5)
    while 1:
        for position in gait.step_generator(reverse=False):
            robot.controller.move_to(position, 50)


def side():
    trotter = Sideways(p0 = Positions.ready2, mag_x=0, mag_y=-30, mag_z=50, step_size=15)
    robot.controller.move_to(Positions.ready2)
    time.sleep(0.5)
    while 1:
        for position in trotter.step_generator(reverse=True):
            robot.controller.move_to(position, 80)

def turn():
    gait = Turn(p0 = Positions.ready2, mag_x=20, mag_y=20, mag_z=40, step_size=15)
    robot.controller.move_to(Positions.ready2)
    time.sleep(0.5)
    while 1:
        for position in gait.step_generator(reverse=False):
            robot.controller.move_to(position, 50)



turn()

