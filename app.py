#!/usr/bin/env python3
"""
Vega Robot Control Interface - NiceGUI Implementation
Converted from HTML template with mock functions for demonstration
"""
import logging
from nicegui import ui, app
from fastapi.responses import StreamingResponse
import asyncio
from typing import Dict, List
from src.agents.yolo_agent import YoloAgent
from src.model.types import MoveTypes
from src.nodes.controller import Controller
from src.nodes.imu import IMU
from src.nodes.navigator import Navigator
from src.nodes.robot import Robot
from settings import settings

logging.basicConfig(level=logging.INFO)

controller = Controller()
imu = IMU()
yolo_agent = YoloAgent()
navigator = Navigator(controller=controller)

robot: Robot = Robot(controller=controller, imu=imu)

# Mock functions for robot control



async def set_pose_command(pose: str):
    """Mock function for setting robot pose"""
    ui.notify(f"Setting pose to {pose}", type='info')
    robot.controller.set_pose(pose)

async def demo_command():
    """Mock function for demo command"""
    ui.notify("Starting demo sequence", type='info')
    robot.demo()

async def auto_level():
    """Mock function for auto level"""
    ui.notify("Auto leveling robot", type='info')
    robot.level()
    
async def reset_offsets():
    ui.notify("Resetting offsets", type='info')
    settings.reset_offsets()

async def handle_stop():
    """Mock function for stop command"""
    ui.notify("Stopping robot", type='warning')
    robot.controller.stop()

async def toggle_navigation(enabled: bool):
    """Toggle autonomous navigation mode"""
    if enabled:
        navigator.start_navigation()
        ui.notify("Navigation mode ON - Robot will avoid obstacles", type='positive')
    else:
        navigator.stop_navigation()
        ui.notify("Navigation mode OFF", type='warning')

async def handle_move(move_type: MoveTypes):
    """Mock function for move command"""
    ui.notify(f"Moving {move_type.value}", type='info')
    robot.controller.process_move(move_type)

def create_data_grid(data_dict: Dict, labels: List[str]):
    """Helper function to create data grids"""
    legs = data_dict.keys()
    
    with ui.grid(columns=4).classes('gap-2 w-full text-sm'):
        # Headers
        ui.label('').classes('compact w-1/4').style('min-height:0.5em; line-height:1; padding:0;')
        for label in labels:
            ui.label(label).classes('font-bold text-center compact w-1/4').style('min-height:0.5em; line-height:1; padding:0;')
        # Data rows
        for leg in legs:
            ui.label(leg).classes('font-bold compact w-1/4').style('min-height:0.5em; line-height:1; padding:0;')
            for key in data_dict[leg]:
                value = data_dict[leg][key]
                if isinstance(value, float):
                    ui.label(f"{value:.0f}" if value == int(value) else f"{value:.2f}") \
                        .classes('text-center compact w-1/4') \
                        .style('font-family: monospace; min-height:0.5em; line-height:1; padding:0;')
                else:
                    ui.label(str(value)) \
                        .classes('text-center compact w-1/4') \
                        .style('font-family: monospace; min-height:0.5em; line-height:1; padding:0;')


def video_frame():
    with ui.column().classes('video-column').style('width: 648px; max-width: 100vw; margin: 0 auto; padding: 0;'):
        ui.html('''
        <style>
        .video-wrap {
            width: 648px;
            height: 368px;
            max-width: 100vw;
            position: relative;
            background: #333;
            overflow: hidden;
            margin: 0 auto;
            padding: 0;
            box-sizing: border-box;
        }
        .video-wrap iframe {
            width: 648px;
            height: 368px;
            border: 0;
            display: block;
            background: #333;
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        .capture-row {
            width: 100%;
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        </style>
        ''', sanitize=False)
        with ui.element('div').classes('video-wrap'):
            ui.html('<iframe src="https://orin1:8554" scrolling="no" allowfullscreen style="width:640px;height:360px"></iframe>', sanitize=False)

@ui.page('/')
async def main_page():
    ui.page_title('Vega Robot Control')
    
    # Main container - side by side on wide screens, stacked on mobile
    with ui.row().classes('gap-4 p-4 w-full flex-wrap'):
        # Left panel - Video stream, sliders, and controls
        with ui.column().classes('flex-1 min-w-[400px] max-w-[700px] p-4 rounded bg-gray-900 text-white items-center'):
            # Video stream
            video_frame()
            
            # Control panel - 3x3 movement buttons
            with ui.grid(columns=3).classes('gap-2 my-4 w-full max-w-[400px]'):
                # Top row
                ui.button(icon="turn_slight_left", on_click=lambda: handle_move(MoveTypes.FORWARD_LT)).classes('bg-blue-600 text-white text-sm px-2 py-1')
                ui.button(icon="arrow_upward", on_click=lambda: handle_move(MoveTypes.FORWARD)).classes('bg-blue-600 text-white text-sm px-2 py-1')
                ui.button(icon="turn_slight_right", on_click=lambda: handle_move(MoveTypes.FORWARD_RT)).classes('bg-blue-600 text-white text-sm px-2 py-1')

                # Middle row
                ui.button(icon="arrow_back", on_click=lambda: handle_move(MoveTypes.LEFT)).classes('bg-blue-600 text-white text-sm px-2 py-1')
                ui.button(icon="stop", on_click=lambda: handle_move(MoveTypes.STOP)).classes('bg-red-600 text-white text-sm px-2 py-1')
                ui.button(icon="arrow_forward", on_click=lambda: handle_move(MoveTypes.RIGHT)).classes('bg-blue-600 text-white text-sm px-2 py-1')

                # Bottom row
                ui.button(icon="turn_slight_left", on_click=lambda: handle_move(MoveTypes.BACKWARD_LT)).classes('bg-blue-600 text-white text-sm px-2 py-1').style('transform: scaleY(-1);')
                ui.button(icon="arrow_downward", on_click=lambda: handle_move(MoveTypes.BACKWARD)).classes('bg-blue-600 text-white text-sm px-2 py-1')
                ui.button(icon="turn_slight_right", on_click=lambda: handle_move(MoveTypes.BACKWARD_RT)).classes('bg-blue-600 text-white text-sm px-2 py-1').style('transform: scaleY(-1);')

            # Prowl controls - stealthy movement
            with ui.row().classes('gap-2 w-full max-w-[400px] justify-center'):
                ui.button('Prowl', icon="arrow_upward", on_click=lambda: handle_move(MoveTypes.PROWL)).classes('bg-purple-700 text-white text-sm px-4 py-1')
                ui.button('Prowl', icon="arrow_downward", on_click=lambda: handle_move(MoveTypes.PROWL_BACKWARD)).classes('bg-purple-700 text-white text-sm px-4 py-1')

            # Navigation mode toggle
            with ui.row().classes('gap-2 w-full max-w-[400px] justify-center items-center mt-4'):
                ui.label('Auto Navigate:').classes('text-sm')
                ui.switch(on_change=lambda e: toggle_navigation(e.value)).classes('text-green-500')
            
            # Sliders (commented out)
            # with ui.row().classes('gap-4 my-4 w-full justify-center'):
            #     with ui.row().classes('items-center'):
            #         ui.label('Height (%)').classes('text-xs mb-2')
            #         height_value_label = ui.label('65').classes('mb-1')
            #         def height_slider_change(e):
            #             height_value_label.set_text(str(e.value))
            #         height_slider = ui.slider(
            #             min=0, max=100, value=65, step=1, on_change=height_slider_change
            #         ).classes('w-24')
            #
            #     with ui.row().classes('items-center'):
            #         ui.label('Tilt (roll)').classes('text-xs mb-2')
            #         yaw_value_label = ui.label('0').classes('mb-1')
            #         def yaw_slider_change(e):
            #             yaw_value_label.set_text(str(e.value))
            #             settings.tilt.yaw = int(e.value)
            #             robot.set_pose("ready")
            #         yaw_slider = ui.slider(
            #             min=-50, max=50, value=0, step=5, on_change=yaw_slider_change
            #         ).classes('w-24')
            #
            #     with ui.row().classes('items-center'):
            #         ui.label('Tilt (pitch)').classes('text-xs mb-2')
            #         pitch_value_label = ui.label('0').classes('mb-1')
            #         def pitch_slider_change(e):
            #             pitch_value_label.set_text(str(e.value))
            #             settings.tilt.pitch = int(e.value)
            #             robot.set_pose("ready")
            #         pitch_slider = ui.slider(
            #             min=-50, max=50, value=0, step=5, on_change=pitch_slider_change
            #         ).classes('w-24')
                    
            # Display values
            with ui.row().classes('justify-between w-full text-sm'):
                ui.label('Heading:')
                heading_display = ui.label('0.0')
                ui.label('Roll:')
                roll_display = ui.label('0.0')
                ui.label('Pitch:')
                pitch_display = ui.label('0.0')
            
            with ui.row().classes('justify-between w-full text-sm'):
                ui.label('Angular Vel:')
                angular_vel_display = ui.label('0.0')
                ui.label('Angular Accel:')
                angular_accel_display = ui.label('0.0')
        
        # Right panel - Commands and data
        with ui.column().classes('flex-1 min-w-[300px] p-4 border rounded gap-4'):
            # ... rest stays the same
            # Command buttons
            ui.label('Poses').classes('text-lg font-bold w-full')
            with ui.grid(columns=3).classes('gap-2 w-full'):
                ui.button('Sit', on_click=lambda: set_pose_command('sit')).classes('bg-green-600 text-white text-sm')
                ui.button('Crouch', on_click=lambda: set_pose_command('crouch')).classes('bg-green-600 text-white text-sm')
                ui.button('Ready', on_click=lambda: set_pose_command('ready')).classes('bg-green-600 text-white text-sm')
            with ui.grid(columns=3).classes('gap-2 w-full'):
                ui.button('Trotting', on_click=lambda: set_pose_command('trotting')).classes('bg-green-600 text-white text-sm')
                ui.button('Walking', on_click=lambda: set_pose_command('walking')).classes('bg-green-600 text-white text-sm')
                ui.button('Demo', on_click=demo_command).classes('bg-green-600 text-white text-sm')
            
            ui.separator()
            
            # Position section
            ui.label('Position').classes('text-lg font-bold')
            position_container = ui.column().classes('w-full')
            
            # Angles section
            ui.label('Angles').classes('text-lg font-bold')
            angles_container = ui.column().classes('w-full')
            
            # Offsets section
            ui.label('Offsets').classes('text-lg font-bold')
            offsets_container = ui.column().classes('w-full')
            
            ui.separator()
            
            # Control buttons
            with ui.row().classes('justify-around w-full'):
                ui.button('Auto Level', on_click=auto_level).classes('bg-blue-600 text-white text-sm')
                ui.button('Reset Offsets', on_click=reset_offsets).classes('bg-blue-600 text-white text-sm')
    
    # Flag to control update loop
    running = True

    def stop_update():
        nonlocal running
        running = False

    app.on_disconnect(stop_update)

    async def update_displays():
        while running:
            # Update main display values
            heading_display.set_text(f"{imu.imu_data.heading:.2f}")
            roll_display.set_text(f"{imu.imu_data.roll:.2f}")
            pitch_display.set_text(f"{imu.imu_data.pitch:.2f}")
            angular_vel_display.set_text(f"{imu.imu_data.angular_vel:.2f}")
            angular_accel_display.set_text(f"{imu.imu_data.angular_accel:.2f}")

            # Update data grids
            position_container.clear()
            with position_container:
                create_data_grid(robot.data.positions, ['X', 'Y', 'Z'])

            angles_container.clear()
            with angles_container:
                create_data_grid(robot.data.angles, ['Coxa', 'Femur', 'Tibia'])

            offsets_container.clear()
            with offsets_container:
                create_data_grid(robot.data.offsets, ['X', 'Y', 'Z'])

            await asyncio.sleep(1.0)  # Update every second

    # Start the update loop
    asyncio.create_task(update_displays())

async def main():
    await asyncio.gather(
        robot.imu.spin(frequency=settings.imu_frequency),
        robot.controller.spin(frequency=settings.robot_frequency),
        navigator.spin(frequency=10),  # Navigation decisions at 10Hz
    )

def start_video():
    yolo_agent.run()


def start_app():
    ui.run(
        title='Vega Robot Control',
        port=8080,
        host='0.0.0.0',
        reload=False,
        show=True
    )

if __name__ == "__main__":
    print("🤖 Starting Vega Robot Control Interface...")
    try:
        import threading

        video_thread = threading.Thread(target=start_video)
        video_thread.daemon = True
        video_thread.start()
        
        app_thread = threading.Thread(target=start_app)
        app_thread.daemon = True
        app_thread.start()    

        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        if yolo_agent:
            yolo_agent.stop()
        import time
        time.sleep(0.3)

    