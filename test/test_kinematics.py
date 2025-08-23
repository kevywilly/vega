from settings import settings
from src.motion.kinematics import QuadrupedKinematics

_km = QuadrupedKinematics(settings.coxa_length, settings.femur_length, settings.tibia_length, settings.robot_width, settings.robot_length)

def test_tilt_yaw():
    position = settings.position_ready
    tilted = _km.tilt(positions=position, pitch=0, yaw=-5)
    assert tilted[0][2] < tilted[2][2]

def test_tilt_pitch():
    position = settings.position_ready
    tilted = _km.tilt(positions=position, pitch=5, yaw=0)
    assert tilted[0][1] < tilted[1][2]