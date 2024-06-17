from robolib.motion.gaits.sideways import Sideways
from robolib.motion.gaits.trot import Trot
from robolib.motion.gaits.turn import Turn
from robolib.settings import settings

from vega.nodes.robot import Robot

robot = Robot()

import time

target = settings.quadruped.position_crouch
num_steps = 54


def demo():
    positions = [settings.quadruped.position_ready, settings.quadruped.position_ready,
                 settings.quadruped.position_ready]
    print(positions)
    for p in positions:
        robot.set_targets(p)
        robot.move_to_targets()
        robot.print_stats()
        time.sleep(2)


def trot():
    gait = Trot(p0=settings.quadruped.position_ready, stride=60, clearance=65, step_size=15)
    robot.controller.move_to(settings.quadruped.position_ready)
    time.sleep(0.5)
    while 1:
        # for position in gait.step_generator(reverse=False):
        #    robot.controller.move_to(position, 10)


def side():
    trotter = Sideways(p0=settings.quadruped.position_ready, stride=30, clearance=50, step_size=15)
    robot.controller.move_to(settings.quadruped.position_ready)
    time.sleep(0.5)
    while 1:
        for position in trotter.step_generator():
            robot.controller.move_to(position, 80)


def turn():
    gait = Turn(degrees=-20, p0=settings.quadruped.position_ready, clearance=80, step_size=10)
    robot.controller.move_to(settings.quadruped.position_ready)
    time.sleep(0.5)
    while 1:
        # for position in gait.step_generator(reverse=False):
        #    robot.controller.move_to(position, 80)

trot()
