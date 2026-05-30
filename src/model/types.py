from enum import Enum

class MoveTypes(str, Enum):
    FORWARD_LT="FORWARD_LT"
    FORWARD="FORWARD"
    FORWARD_RT = "FORWARD_RT"
    LEFT = "LEFT"
    STOP = "STOP"
    RIGHT = "RIGHT"
    BACKWARD_LT = "BACKWARD_LT"
    BACKWARD = "BACKWARD"
    BACKWARD_RT = "BACKWARD_RT"
    TROT_IN_PLACE = "TROT_IN_PLACE"
    PROWL = "PROWL"
    PROWL_BACKWARD = "PROWL_BACKWARD"
    # Experimental turn gaits (A/B comparison vs legacy Turn) -- see
    # docs/ideation/2026-05-30-better-turn-gait.md
    SIMPLE_TURN_LT = "SIMPLE_TURN_LT"
    SIMPLE_TURN_RT = "SIMPLE_TURN_RT"
    ARC_TURN_LT = "ARC_TURN_LT"
    ARC_TURN_RT = "ARC_TURN_RT"
