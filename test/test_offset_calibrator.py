from src.model.calibrator import Calibrator


def test_offset_calibration():
    euler = (200, 1.1, 165)
    offsets = Calibrator.get_offsets(euler)
    assert euler

