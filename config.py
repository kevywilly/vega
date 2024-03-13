import numpy as np

coxa = 50
femur = 102
tibia = 114
max_height = femur+tibia

servos = np.array([[11,12,13],[21,22,23],[31,32,33],[41,42,43]])
servo_ids = servos.reshape(-1)

a_zero = np.radians(np.array([2, 90, 30]))

a_home = np.zeros((4,3))
p_home = np.array([[0, 0, 114+102], [0, 0, 114+102], [0, 0, 114+102], [0, 0, 114+102]])
p_ready = p_home * 0.75
p_crouch = p_home * 0.33
flip = [[1,1,1],[-1,-1,-1],[-1,-1,-1],[1,1,1]]



