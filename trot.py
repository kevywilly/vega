from src.nodes.robot import Robot 
from src.motion.gaits.trot import Trotter, Trot
from config import Positions
robot = Robot()

import time
target = Positions.crouch
num_steps = 54
import numpy as np

trotter = Trot(mag_x=60, mag_y=0, mag_z=60, step_size=15)

def demo():
    positions = [Positions.ready, Positions.crouch, Positions.ready]
    print(positions)
    for p in positions:
        robot.set_targets(p)
        robot.move_to_targets()
        robot.print_stats()
        time.sleep(2)

def walk():
    p = Positions.ready
    
    for i in range(num_steps):
        position = np.array([trotter.get_step(i) + p[0], p[1],p[2],p[3]])
        print(position)
        robot.controller.move_to(position,1)
            

def walk2():
    p = Positions.ready
    while 1:
        for position in trotter.step_generator():
            position = position + Positions.ready
            
            robot.controller.move_to(position,50)        


walk2()