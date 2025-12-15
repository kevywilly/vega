# Graveyard

This folder contains code that has been retired from the main codebase but preserved for reference.

## Contents

### gaits/
Unused or experimental gait implementations:
- `turning_gait.py` - Alternative turning implementation (never used)
- `sidestep.py` - Old sidestep (replaced by SimpleSidestep)
- `jump.py` - Jump gait (unused)
- `tiger_run.py` - Sequential leg pattern (unused)
- `trot_with_lateral.py` - Old trot with lateral (replaced by SimpleTrotWithLateral)
- `experimental_gaits.py` - Experimental SimplifiedGait implementations (SimpleTrot, SimpleWalk, SimpleProwl, SimpleJump, SimpleTurn, SimpleTrotWithLateralFixed)

### agents/
- `video_agent.py` - VideoStream class (replaced by YoloAgent)
- `vc.py` - Video capture utilities

### nodes/
- `camera.py` - Camera node (unused)

### interfaces/
- `msgs.py` - ROS-like message types (never integrated)
- `vector.py` - Vector utilities

### scripts/
Development and test scripts:
- `yolo*.py` - YOLO experiments
- `test_*.py` - Gait test scripts
- `summary.py`, `run_gaits.py`, `orin.py` - Dev utilities
- `imu_test.py`, `testvideo.py`, `testservo.py` - Hardware test scripts

### utils/
- `gait_plotting.py` - Visualization utilities for gaits

## Recovery

To restore any file, simply move it back to its original location and update the relevant `__init__.py` files.
