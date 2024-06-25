import time

from config import POSITIONS
from src.motion.gaits.gait import Gait
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
        robot.print_stats()
        time.sleep(2)


def run(gait: Gait):
    robot.controller.move_to(POSITIONS.READY)
    time.sleep(0.5)
    positions = POSITIONS.READY
    while positions is not None:
        robot.controller.move_to(positions, 50)
        positions = next(gait)

run(Trot2(p0=POSITIONS.READY, stride=60, clearance=65, step_size=10))
# run(Turn(degrees=-20, p0=POSITIONS.READY, clearance=80, step_size=10))
# run(Sidestep(p0=POSITIONS.READY, stride=30, clearance=50, step_size=15))

