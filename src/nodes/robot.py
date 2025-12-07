from dataclasses import dataclass, field
import time

import numpy as np

from settings import settings
from src.interfaces.pose import Pose
from src.model.types import MoveTypes
from src.motion.gaits.gait import Gait
from src.motion.gaits.simplified_gait import (
    SimpleTrotWithLateral, SimpleSidestep
)
from src.motion.gaits.trot import Trot
from src.motion.gaits.turn import Turn

# from src.nodes.camera import Camera
from src.nodes.controller import Controller
from src.nodes.imu import IMU
from src.nodes.node import Node
#from src.vision.image import Image, ImageUtils
from dataclasses import replace

class Image:
    value = None

def _array_to_dict(ar, label: str = "Leg"):
    return {
        f"{label} {i}": {"x": float(x), "y": float(y), "z": z}
        for i, (x, y, z) in enumerate(ar)
    }


@dataclass
class RobotData:
    heading: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    angular_vel: float = 0.0
    angular_accel: float = 0.0
    positions: dict = field(default_factory=lambda: _array_to_dict(Pose().positions))
    angles: dict = field(
        default_factory=lambda: _array_to_dict(Pose().angles_in_degrees)
    )
    offsets: dict = field(
        default_factory=lambda: _array_to_dict(settings.default_position_offsets)
    )
    moving: bool = False
    move_type: MoveTypes = MoveTypes.STOP


class Robot(Node):

    def __init__(self, **kwargs):
        super(Robot, self).__init__(**kwargs)

        # initialize objects
        self.session_id = str(int(time.time()))
        self.gait: Gait | None = None
        self.image: Image = Image()
        self.cmd_zero = True
        self.moving: bool = False
        self.move_type: MoveTypes = MoveTypes.STOP
        self.roll_offsets: np.ndarray = np.zeros((4, 3))
        self.pitch_offsets: np.ndarray = np.zeros((4, 3))

        # initialize nodes
        try:
            print("skipping camera")
            self.camera = None
            #self.camera: Optional[Camera] = Camera()
        except Exception as ex:
            self.logger.error(ex.__str__())
            self.camera = None

        self.controller: Controller = Controller(frequency=30)

        self.imu = IMU()

        time.sleep(0.2)

        self.auto_level()

        self.loaded()

    def _start_nodes(self):
        pass
        #self.imu.spin(frequency=5)
        #self.controller.spin()
        # if self.camera:
        #    self.camera.spin()


    def get_image(self):
        return self.image.value

    def get_imu(self):
        return self.imu.euler

    def set_targets(self, positions: np.ndarray):
        return self.controller.set_targets(positions)

    def move_to_targets(self, millis:int = 0):
        return self.controller.move_to_targets(millis)

    def get_stream(self):
        while True:
            # ret, buffer = cv2.imencode('.jpg', frame)
            try:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + self.get_image() + b"\r\n"
                )  # concat frame one by one and show result
            except Exception:
                pass

    def stop(self):
        self.moving = False
        self.move_type = MoveTypes.STOP
        self.ready()
        return {"moving": self.moving, "move_type": self.move_type}

    def process_move(self, move_type: MoveTypes):
        if move_type == MoveTypes.FORWARD:
            self.gait = SimpleTrotWithLateral(
                p0=settings.position_trot + settings.position_forward_offsets,
                params=settings.trot_params
            )
        elif move_type == MoveTypes.FORWARD_LT:
            self.gait = Turn(params=replace(settings.turn_params, turn_direction=1))
        elif move_type == MoveTypes.FORWARD_RT:
            self.gait = Turn(params=replace(settings.turn_params, turn_direction=-1))
        elif move_type == MoveTypes.BACKWARD:
            self.gait = SimpleTrotWithLateral(
                p0=settings.position_trot + settings.position_backward_offsets,
                params=settings.trot_reverse_params,
            )
        elif move_type == MoveTypes.BACKWARD_LT:
            self.gait = Turn(
                params=replace(settings.turn_params, turn_direction=-1, is_reversed=True)
            )
        elif move_type == MoveTypes.BACKWARD_RT:
            self.gait = Turn(params=replace(settings.turn_params, turn_direction=1, is_reversed=True))
        elif move_type == MoveTypes.LEFT:
            self.gait = SimpleSidestep(params=replace(settings.sidestep_params, is_reversed=True))
        elif move_type == MoveTypes.RIGHT:
            self.gait = SimpleSidestep(params=settings.sidestep_params)
        elif move_type == MoveTypes.TROT_IN_PLACE:
            self.gait = Trot(params=settings.trot_in_place_params)
        elif move_type == MoveTypes.STOP:
            return self.stop()

        self.move_type = move_type

        if self.move_type != MoveTypes.STOP:
            self.moving = True

        return {"moving": self.moving, "move_type": self.move_type}

    def demo(self):
        positions = [
            settings.position_ready,
            settings.position_crouch,
            settings.position_ready,
            settings.position_sit,
        ]

        for p in positions:
            self.set_targets(p)
            self.move_to_targets()
            time.sleep(2)

    def trot_in_place(self):
        gait = Trot(params=settings.trot_in_place_params)
        self.ready(200)
        self.logger.info("Trotting in place...")
        for i in range(int(gait.shape[0] * 2)):
            position = next(gait)
            self.controller.move_to(position, 10)
        self.logger.info("Done trotting in place...")
        time.sleep(0.1)

    def auto_level(self):
        if settings.auto_level:
            for i in range(3):
                self.logger.info(f"*** Leveling pass {i} ***")
                if self.level():
                    return



    def ready(self, millis=200):
        self.controller.move_to(settings.position_ready, millis)

    def set_pose(self, pose: str):
        v = pose.lower()

        p = None

        if v == "ready":
            p = settings.position_ready
        elif v == "sit":
            p = settings.position_sit
        elif v == "crouch":
            p = settings.position_crouch
        elif v == "walking":
            p = settings.position_walk
        elif v == "trotting":
            p = settings.position_trot
        else:
            return {"status": "error, unknown pose"}

        if self.moving:
            self.stop()
            time.sleep(0.5)

        self.set_targets(p)
        self.move_to_targets()

    @property
    def data(self) -> RobotData:
        pose = self.controller.pose
        return RobotData(
            heading=self.imu.euler[0],
            roll=self.imu.euler[1],
            pitch=self.imu.euler[2],
            angular_vel=self.imu.gyro[2],
            angular_accel=self.imu.acceleration[2],
            positions={
                f"Leg {i}": {"x": pos[0], "y": pos[1], "z": pos[2]}
                for i, pos in enumerate(pose.positions)
            },
            angles={
                f"Leg {i}": {"coxa": angle[0], "femur": angle[1], "tibia": angle[2]}
                for i, angle in enumerate(pose.angles_in_degrees)
            },
            offsets={
                f"Leg {i}": {"x": offset[0], "y": offset[1], "z": offset[2]}
                for i, offset in enumerate(settings.position_offsets)
            },
            moving=self.moving,
            move_type=self.move_type,
        )

    def spinner(self):
        """Optimized main control loop - minimizes overhead in hot path."""
        if self.moving and self.gait is not None:
            # Hot path: get next position and send to servos
            # next() is already optimized in Gait class
            position = next(self.gait)
            # time=0 means immediate move, no interpolation delay
            self.controller.move_to(position, 0)

    def level(self) -> bool:
        self.logger.info("**** Performing Level Calibration ***")
        try:
            self.trot_in_place()
            self.ready(100)
            time.sleep(0.2)

            
            pitch_array = np.array([-1, -1, 1, 1])
            roll_array = np.array([1, -1, -1, 1])
            zeros = np.zeros(4)
            
            
            
            for i in range(10):
                heading, roll, pitch = self.imu.sensor.euler

                print(f"roll: {roll:.2f}, pitch: {pitch:.2f}")


                # Fix one axis at a time, prioritize the larger error
                #if abs(pitch) > abs(roll) and abs(pitch) > settings.pitch_threshold:
                #    offset = pitch_array if pitch >= 0 else -pitch_array
                if roll is not None and abs(roll) > settings.roll_threshold:
                    offset = roll_array if roll >= 0 else -roll_array
                    settings.position_offsets[:, 2] += offset.astype(int)
                    print(f"offset => {settings.position_offsets[:, 2].tolist()}")
                else:
                    print(f"leveling succeeded! roll: {roll:.2f}, pitch: {pitch:.2f}")
                    return True
                
                self.ready(10)
                time.sleep(0.3)


        except Exception as ex:
            self.ready(200)
            self.logger.error(ex)

        self.logger.info(f"leveling failed... roll: {roll:.2f}, pitch: {pitch:.2f}")
        settings.reset_offsets()
        self.ready(200)
        return False