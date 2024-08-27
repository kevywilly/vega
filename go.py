import time

from settings import settings
from src.motion.gaits.gait import Gait
from src.motion.gaits.tiger_run import TigerRun
from src.motion.gaits.jump import Jump

from src.nodes.robot import Robot

robot = Robot()


def demo():
    positions = [settings.position_ready, settings.position_crouch, settings.position_ready]
    print(positions)
    for p in positions:
        robot.set_targets(p)
        robot.move_to_targets()
        time.sleep(2)


def run(gait: Gait):
    robot.controller.move_to(gait.p0)
    time.sleep(0.5)
    positions = gait.p0
    while positions is not None:
        robot.controller.move_to(positions, 50)
        positions = next(gait)


# run(Trot(stride=60, clearance=60, step_size=25))
#run(TigerRun(
#        p0=settings.position_ready,
#        stride=70,  # Increase stride length for a more dynamic run
#        clearance=70,  # Increase clearance for higher leg lift
#        step_size=5  # Adjust step size for smoother transitions
#    ))

run(Jump(
        p0=settings.position_crouch,
        stride=0,  # No forward movement
        clearance=60,  # Height of the jump
        step_size=1
    ))

# run(Turn(degrees=-20, p0=POSITIONS.READY, clearance=80, step_size=10))
# run(Sidestep(p0=POSITIONS.READY, stride=30, clearance=50, step_size=15))
