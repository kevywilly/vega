from settings import settings
from src.motion.kinematics import QuadrupedKinematics
import numpy as np


_km = QuadrupedKinematics(settings.coxa_length, settings.femur_length, settings.tibia_length, settings.robot_width, settings.robot_length)

def test_forward_kinematics():
    result = _km.forward_kinematics(settings.position_ready[0]).astype(int)
    assert sum(result - np.array([-37,0,94]).astype(int)) == 0
    print(result)
    assert result is not None

def test_inverse_kinematics():
    angles = np.array([-37, 0, 94])
    result = _km.inverse_kinematics(angles).astype(int)
    assert sum(result - np.array([0,0,2])) == 0
