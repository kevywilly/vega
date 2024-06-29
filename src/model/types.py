from enum import Enum

class MoveTypes(str, Enum):
    FORWARD_LT="FORWARD_LT"
    FORWARD="FORWARD"
    FORWARD_RT = "FORWARD_RT"
    LEFT = "FORWARD_LT"
    STOP = "STOP"
    RIGHT = "RIGHT"
    BACKWARD_LT = "BACKWARD_LT"
    BACKWARD = "BACKWARD"
    BACKWARD_RT = "BACKWARD_RT"