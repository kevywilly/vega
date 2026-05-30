from collections import deque
from src.model.types import MoveTypes
from src.nodes.node import Node
from src.signals import Topics


class Navigator(Node):
    """
    Autonomous navigation node using YOLO obstacle detection.

    Subscribes to obstacle detections and controls robot movement
    to avoid obstacles while preferring forward motion.
    """

    def __init__(self, controller, **kwargs):
        super(Navigator, self).__init__(**kwargs)
        self.controller = controller
        self.active = False
        self.turn_bias = 0  # -1=prefer left, 0=neutral, +1=prefer right
        self.turn_history = deque(maxlen=10)
        self.last_obstacles = {}
        self.frames_since_direction_change = 0

    def start_navigation(self):
        """Activate autonomous navigation mode."""
        if self.active:
            return
        self.active = True
        self.turn_bias = 0
        self.turn_history.clear()
        self.last_obstacles = {}
        self.frames_since_direction_change = 0
        Topics.obstacles.connect(self.on_obstacles)
        self.logger.info("Navigation mode activated")

    def stop_navigation(self):
        """Deactivate autonomous navigation mode."""
        if not self.active:
            return
        self.active = False
        Topics.obstacles.disconnect(self.on_obstacles)
        self.controller.stop()
        self.logger.info("Navigation mode deactivated")

    def on_obstacles(self, sender, payload: dict):
        """Handle incoming obstacle detection data."""
        self.last_obstacles = payload

    def _record_turn(self, direction: int):
        """Record a turn decision and update bias."""
        self.turn_history.append(direction)
        # Update bias based on recent history
        if len(self.turn_history) >= 3:
            recent = list(self.turn_history)[-3:]
            if all(d < 0 for d in recent):
                self.turn_bias = -1
            elif all(d > 0 for d in recent):
                self.turn_bias = 1

    def _decide_movement(self, obstacles: dict) -> MoveTypes:
        """
        Decide which movement to make based on detected obstacles.

        Priority:
        1. Go forward if path is clear
        2. Turn toward the clearer side if center is blocked
        3. Use turn bias to avoid oscillation
        """
        lower_left = obstacles.get('lower_left', 0)
        lower_center = obstacles.get('lower_center', 0)
        lower_right = obstacles.get('lower_right', 0)

        # Also consider upper regions for lookahead
        upper_left = obstacles.get('upper_left', 0)
        upper_center = obstacles.get('upper_center', 0)
        upper_right = obstacles.get('upper_right', 0)

        # Path completely clear - go forward
        if lower_center == 0 and lower_left == 0 and lower_right == 0:
            # Reset bias slowly when path is clear
            if self.frames_since_direction_change > 20:
                self.turn_bias = 0
            return MoveTypes.FORWARD

        # Lower center blocked - must turn
        if lower_center > 0:
            # Calculate "openness" of each side (fewer obstacles = more open)
            left_score = lower_left + upper_left * 0.5
            right_score = lower_right + upper_right * 0.5

            # Direction change cooldown to prevent oscillation
            min_frames_before_switch = 15

            if left_score < right_score:
                # Left is clearer
                if self.turn_bias > 0 and self.frames_since_direction_change < min_frames_before_switch:
                    # Committed to right, stick with it briefly
                    return MoveTypes.FORWARD_RT
                self._record_turn(-1)
                self.frames_since_direction_change = 0
                return MoveTypes.FORWARD_LT
            elif right_score < left_score:
                # Right is clearer
                if self.turn_bias < 0 and self.frames_since_direction_change < min_frames_before_switch:
                    # Committed to left, stick with it briefly
                    return MoveTypes.FORWARD_LT
                self._record_turn(1)
                self.frames_since_direction_change = 0
                return MoveTypes.FORWARD_RT
            else:
                # Equal - use bias to maintain consistency
                if self.turn_bias <= 0:
                    self._record_turn(-1)
                    return MoveTypes.FORWARD_LT
                else:
                    self._record_turn(1)
                    return MoveTypes.FORWARD_RT

        # Only lower left blocked - turn right
        if lower_left > 0 and lower_right == 0:
            return MoveTypes.FORWARD_RT

        # Only lower right blocked - turn left
        if lower_right > 0 and lower_left == 0:
            return MoveTypes.FORWARD_LT

        # Both sides have obstacles but center is clear - go forward carefully
        if lower_center == 0:
            return MoveTypes.FORWARD

        # Fallback: use bias
        if self.turn_bias <= 0:
            return MoveTypes.FORWARD_LT
        return MoveTypes.FORWARD_RT

    def spinner(self):
        """Main navigation loop - called at node frequency."""
        if not self.active:
            return

        self.frames_since_direction_change += 1

        obstacles = self.last_obstacles
        if not obstacles:
            # No detection data yet - stay still or continue forward
            return

        move = self._decide_movement(obstacles)

        # Only send command if movement type changed
        if move != self.controller.move_type:
            self.logger.debug(f"Navigation: {move.value} (obstacles: {obstacles})")
            self.controller.process_move(move)
