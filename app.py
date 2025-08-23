#!/usr/bin/env python3
"""
Vega Robot Control Interface - NiceGUI Implementation
Converted from HTML template with mock functions for demonstration
"""

from nicegui import ui, app
import asyncio
from typing import Dict, List
from src.nodes.robot import Robot
from settings import settings

robot: Robot = Robot()

# Mock functions for robot control
async def sit_command():
    """Mock function for sit command"""
    ui.notify("Robot sitting down", type='info')
    robot.set_pose("sit")

async def crouch_command():
    """Mock function for crouch command"""
    ui.notify("Robot crouching", type='info')
    robot.set_pose("crouch")

async def ready_command():
    """Mock function for ready command"""
    ui.notify("Robot ready position", type='info')
    robot.set_pose("ready")

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
    
def height_slider_change(e):
    """Mock function for height slider"""
    print(f"Height slider changed to: {e.value}")

def yaw_slider_change(e):
    """Mock function for yaw slider"""
    settings.tilt.yaw = int(e.value)
    print(f"Yaw slider changed to: {e.value}")

def pitch_slider_change(e):
    """Mock function for pitch slider"""
    settings.tilt.pitch = int(e.value)
    print(f"Pitch slider changed to: {e.value}")

def create_data_grid(data_dict: Dict, labels: List[str]):
    """Helper function to create data grids"""
    legs = data_dict.keys()
    
    with ui.grid(columns=4).classes('gap-8 w-full text-sm'):
        # Headers
        ui.label('')
        for label in labels:
            ui.label(label).classes('font-bold text-center')
        
        # Data rows
        for leg in legs:
            ui.label(leg).classes('font-bold')
            for key in data_dict[leg]:
                value = data_dict[leg][key]
                if isinstance(value, float):
                    ui.label(f"{value:.0f}" if value == int(value) else f"{value:.2f}").classes('text-center').style('font-family: monospace')
                else:
                    ui.label(str(value)).classes('text-center').style('font-family: monospace')

@ui.page('/')
async def main_page():
    ui.page_title('Vega Robot Control')
    
    with ui.row().classes('gap-4 p-4 w-full'):
        # Left panel - Video stream and controls
        with ui.column().classes('w-1/2 p-4 rounded bg-gray-900 text-white'):
            # Mock video stream (placeholder image)
            ui.html('<div class="w-full aspect-video bg-gray-700 flex items-center justify-center text-white">Video Stream Placeholder</div>')
            
            # Control panel - 3x3 movement buttons
            with ui.grid(columns=3).classes('gap-2 my-4'):
                # Top row
                ui.button('Forward LT', on_click=lambda: ui.notify('Forward Left Turn')).classes('bg-blue-600 text-white text-sm px-2 py-1')
                ui.button('Forward', on_click=lambda: ui.notify('Forward')).classes('bg-blue-600 text-white text-sm px-2 py-1')
                ui.button('Forward RT', on_click=lambda: ui.notify('Forward Right Turn')).classes('bg-blue-600 text-white text-sm px-2 py-1')
                
                # Middle row
                ui.button('Left', on_click=lambda: ui.notify('Turn Left')).classes('bg-blue-600 text-white text-sm px-2 py-1')
                ui.button('Stop', on_click=lambda: ui.notify('Stop')).classes('bg-red-600 text-white text-sm px-2 py-1')
                ui.button('Right', on_click=lambda: ui.notify('Turn Right')).classes('bg-blue-600 text-white text-sm px-2 py-1')
                
                # Bottom row
                ui.button('Backward LT', on_click=lambda: ui.notify('Backward Left Turn')).classes('bg-blue-600 text-white text-sm px-2 py-1')
                ui.button('Backward', on_click=lambda: ui.notify('Backward')).classes('bg-blue-600 text-white text-sm px-2 py-1')
                ui.button('Backward RT', on_click=lambda: ui.notify('Backward Right Turn')).classes('bg-blue-600 text-white text-sm px-2 py-1')
            
            # Display values
            with ui.row().classes('justify-between w-full text-sm'):
                ui.label('Heading:')
                heading_display = ui.label('0.0')
                ui.label('Pitch:')
                pitch_display = ui.label('0.0')
                ui.label('Yaw:')
                yaw_display = ui.label('0.0')
            
            with ui.row().classes('justify-between w-full text-sm'):
                ui.label('Angular Vel:')
                angular_vel_display = ui.label('0.0')
                ui.label('Angular Accel:')
                angular_accel_display = ui.label('0.0')
        
        # Middle panel - Vertical sliders
        with ui.column().classes('p-4 border rounded gap-6'):
            with ui.column().classes('items-center'):
                ui.label('Height (%)').classes('text-xs mb-2')
                height_slider = ui.slider(
                    min=0, max=100, value=65, step=1, on_change=height_slider_change
                ).classes('w-32').style('transform: rotate(90deg); transform-origin: center; height: 32px; margin: 50px 0;')
            
            with ui.column().classes('items-center'):
                ui.label('Tilt (yaw)').classes('text-xs mb-2')
                yaw_slider = ui.slider(
                    min=-50, max=50, value=0, step=5, on_change=yaw_slider_change
                ).classes('w-32').style('transform: rotate(90deg); transform-origin: center; height: 32px; margin: 50px 0;')
            
            with ui.column().classes('items-center'):
                ui.label('Tilt (pitch)').classes('text-xs mb-2')
                pitch_slider = ui.slider(
                    min=-50, max=50, value=0, step=5, on_change=pitch_slider_change
                ).classes('w-32').style('transform: rotate(90deg); transform-origin: center; height: 32px; margin: 50px 0;')
        
        # Right panel - Commands and data
        with ui.column().classes('p-4 border rounded gap-4 flex-grow'):
            # Command buttons
            with ui.grid(columns=4).classes('gap-4'):
                ui.button('Sit', on_click=sit_command).classes('bg-green-600 text-white text-sm')
                ui.button('Crouch', on_click=crouch_command).classes('bg-green-600 text-white text-sm')
                ui.button('Ready', on_click=ready_command).classes('bg-green-600 text-white text-sm')
                ui.button('Demo', on_click=demo_command).classes('bg-green-600 text-white text-sm')
            
            ui.separator()
            
            # Position section
            ui.label('Position').classes('text-lg font-bold')
            position_container = ui.column()
            
            # Angles section
            ui.label('Angles').classes('text-lg font-bold')
            angles_container = ui.column()
            
            # Offsets section
            ui.label('Offsets').classes('text-lg font-bold')
            offsets_container = ui.column()
            
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
            #await mock_get_stats()

            # Update main display values
            heading_display.set_text(f"{robot.data.heading:.2f}")
            pitch_display.set_text(f"{robot.data.pitch:.2f}")
            yaw_display.set_text(f"{robot.data.yaw:.2f}")
            angular_vel_display.set_text(f"{robot.data.angular_vel:.2f}")
            angular_accel_display.set_text(f"{robot.data.angular_accel:.2f}")

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

if __name__ in {"__main__", "__mp_main__"}:
    robot.spin(frequency=50)
    ui.run(
        title='Vega Robot Control',
        port=8080,
        host='0.0.0.0',
        reload=True,
        show=True
    )