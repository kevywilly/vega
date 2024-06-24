import time

from config import POSITIONS
from src.motion.gaits.sidestep import Sidestep
from src.motion.gaits.trot import Trot
from src.motion.gaits.turn import Turn
from src.motion.gaits.trot2 import Trot2
from src.nodes.robot import Robot

robot = Robot()

target = POSITIONS.CROUCH
num_steps = 54


def demo():
    positions = [POSITIONS.READY, POSITIONS.CROUCH, POSITIONS.READY]
    print(positions)
    for p in positions:
        robot.set_targets(p)
        robot.move_to_targets()
        time.sleep(2)


def trot():
    gait = Trot(p0=POSITIONS.READY, stride=60, clearance=65, step_size=15)
    robot.controller.move_to(POSITIONS.READY)
    time.sleep(0.5)
    while 1:
        for position in gait.step_generator(reverse=False):
            robot.controller.move_to(position, 50)


def trot2():
    gait = Trot2(p0=POSITIONS.READY, stride=60, clearance=65, step_size=15)
    robot.controller.move_to(POSITIONS.READY)
    time.sleep(0.5)
    while 1:
        for position in gait.step_generator(reverse=False):
            robot.controller.move_to(position, 50)

def side():
    trotter = Sidestep(p0=POSITIONS.READY, stride=30, clearance=50, step_size=15)
    robot.controller.move_to(POSITIONS.READY)
    time.sleep(0.5)
    while 1:
        for position in trotter.step_generator():
            robot.controller.move_to(position, 80)


def turn():
    gait = Turn(degrees=-20, p0=POSITIONS.READY, clearance=80, step_size=10)
    robot.controller.move_to(POSITIONS.READY)
    time.sleep(0.5)
    while 1:
        for position in gait.step_generator(reverse=False):
            robot.controller.move_to(position, 80)


trot2()
