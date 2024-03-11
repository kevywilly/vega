from math import sin, cos
from servo_controller import ServoController
import time
import numpy as np
from serial import Serial

port = Serial('/dev/serial0')

controller = ServoController(serial=port)


servos = np.array([[11,12,13],[21,22,23],[31,32,33],[41,42,43]])
servo_ids = servos.reshape(-1)

positions = controller.get_positions(servo_ids)
print(positions)

home = np.zeros((4,3))
ready = np.array([[2,-65,65],[2,-65,65],[2,-65,65],[2,-65,65]])
crouch = np.array([[2,-90,90],[2,-90,90],[2,-90,90],[2,-90,90]])
crouch2 = np.array([[2,-45,90],[2,-45,90],[2,-45,90],[2,-45,90]])

flip = [[1,1,1],[-1,-1,-1],[-1,-1,-1],[1,1,1]]
step1 = ready + [[0,0,0],[0,0,0],[0,-20,20],[0,0,0]]
step2 = step1 + [[0,0,0],[0,0,0],[0,30,20],[0,0,0]]
step3 = step2 + [[0,0,0],[0,0,0],[0,0,-30],[0,0,0]]


def goto_position(pos: np.ndarray):
        move2 = dict(zip(servos.reshape(-1),((pos*4*flip)+500).reshape(-1)))
        controller.move(move2, 800)
        return move2


while True:
        goto_position(ready)
        time.sleep(1)
        goto_position(crouch)
        time.sleep(1)


"""
q1 = 1
q2 = -1
q3 = -1
q4 = 1

11 - 345, 610 (-155,+110)
12 - 50, 1000 (-450, +500)
13 - 0, 900

21 - 390, 655 (-110, +155)
22 - 0, 950 (-500, 450)
23 - 100, 1000

31 - 390, 655 (-110, +155)
32 - 0, 950 (-500, 450)
33 - 100, 1000

41 - 345, 610 (-155,+110)
42 - 50, 1000 (-450, +500)
43 - 0, 900
"""