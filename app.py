#!/usr/bin/env python3
"""
Vega Robot Control Interface - NiceGUI Implementation
Converted from HTML template with mock functions for demonstration
"""

from nicegui import ui, app
import asyncio
from typing import Dict, List
import random

# Mock data structures
class RobotData:
    def __init__(self):
        self.heading = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.angular_vel = 0.0
        self.angular_accel = 0.0
        self.positions = {
            'Leg 0': {'x': 0.0, 'y': 0.0, 'z': 140.0},
            'Leg 1': {'x': 0.0, 'y': 0.0, 'z': 140.0},
            'Leg 2': {'x': 0.0, 'y': 0.0, 'z': 140.0},
            'Leg 3': {'x': 0.0, 'y': 0.0, 'z': 140.0},
        }
        self.angles = {
            'Leg 0': {'coxa': 0.0, 'femur': 21.0, 'tibia': 124.0},
            'Leg 1': {'coxa': 0.0, 'femur': 36.0, 'tibia': 99.0},
            'Leg 2': {'coxa': 0.0, 'femur': 54.0, 'tibia': 66.0},
            'Leg 3': {'coxa': 0.0, 'femur': 36.0, 'tibia': 99.0},
        }
        self.offsets = {
            'Leg 0': {'x': 0.0, 'y': 0.0, 'z': -40.0},
            'Leg 1': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'Leg 2': {'x': 0.0, 'y': 0.0, 'z': 40.0},
            'Leg 3': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        }

# Global robot data instance
robot_data = RobotData()

# Mock functions for robot control
async def mock_sit_command():
    """Mock function for sit command"""
    ui.notify("Robot sitting down", type='info')
    print("Executing sit command")

async def mock_crouch_command():
    """Mock function for crouch command"""
    ui.notify("Robot crouching", type='info')
    print("Executing crouch command")

async def mock_ready_command():
    """Mock function for ready command"""
    ui.notify("Robot ready position", type='info')
    print("Executing ready command")

async def mock_demo_command():
    """Mock function for demo command"""
    ui.notify("Starting demo sequence", type='info')
    print("Executing demo command")

async def mock_auto_level():
    """Mock function for auto level"""
    ui.notify("Auto leveling robot", type='info')
    print("Executing auto level")

async def mock_reset_offsets():
    """Mock function for reset offsets"""
    ui.notify("Resetting offsets", type='info')
    print("Resetting all offsets to zero")
    for leg in robot_data.offsets:
        for axis in robot_data.offsets[leg]:
            robot_data.offsets[leg][axis] = 0.0

def mock_height_slider_change(value: float):
    """Mock function for height slider"""
    print(f"Height slider changed to: {value}")

def mock_yaw_slider_change(value: float):
    """Mock function for yaw slider"""
    robot_data.yaw = value
    print(f"Yaw slider changed to: {value}")

def mock_pitch_slider_change(value: float):
    """Mock function for pitch slider"""
    robot_data.pitch = value
    print(f"Pitch slider changed to: {value}")

async def mock_get_stats():
    """Mock function to simulate getting robot stats"""
    # Simulate changing data
    robot_data.heading += random.uniform(-1, 1)
    robot_data.angular_vel = random.uniform(-2, 2)
    robot_data.angular_accel = random.uniform(-1, 1)
    
    # Simulate some position changes
    for leg in robot_data.positions:
        for axis in ['x', 'y', 'z']:
            robot_data.positions[leg][axis] += random.uniform(-0.1, 0.1)
            robot_data.angles[leg][list(robot_data.angles[leg].keys())[0]] += random.uniform(-0.5, 0.5)

def create_data_grid(data_dict: Dict, labels: List[str]):
    """Helper function to create data grids"""
    legs = ['Leg 0', 'Leg 1', 'Leg 2', 'Leg 3']
    
    with ui.grid(columns=4).classes('gap-2 w-full text-sm'):
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
        with ui.row().classes('p-4 border rounded gap-6'):
            with ui.column().classes('items-center'):
                ui.label('Height (%)').classes('text-xs mb-2')
                height_slider = ui.slider(
                    min=0, max=100, value=65, step=1
                ).classes('w-32').style('transform: rotate(-90deg); transform-origin: center; height: 32px; margin: 50px 0;').on('update:model-value', mock_height_slider_change)
            
            with ui.column().classes('items-center'):
                ui.label('Tilt (yaw)').classes('text-xs mb-2')
                yaw_slider = ui.slider(
                    min=-180, max=180, value=0, step=1
                ).classes('w-32').style('transform: rotate(-90deg); transform-origin: center; height: 32px; margin: 50px 0;').on('update:model-value', mock_yaw_slider_change)
            
            with ui.column().classes('items-center'):
                ui.label('Tilt (pitch)').classes('text-xs mb-2')
                pitch_slider = ui.slider(
                    min=-90, max=90, value=0, step=1
                ).classes('w-32').style('transform: rotate(-90deg); transform-origin: center; height: 32px; margin: 50px 0;').on('update:model-value', mock_pitch_slider_change)
        
        # Right panel - Commands and data
        with ui.column().classes('p-4 border rounded gap-4 flex-grow'):
            # Command buttons
            with ui.grid(columns=4).classes('gap-4'):
                ui.button('Sit', on_click=mock_sit_command).classes('bg-green-600 text-white text-sm')
                ui.button('Crouch', on_click=mock_crouch_command).classes('bg-green-600 text-white text-sm')
                ui.button('Ready', on_click=mock_ready_command).classes('bg-green-600 text-white text-sm')
                ui.button('Demo', on_click=mock_demo_command).classes('bg-green-600 text-white text-sm')
            
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
                ui.button('Auto Level', on_click=mock_auto_level).classes('bg-blue-600 text-white text-sm')
                ui.button('Reset Offsets', on_click=mock_reset_offsets).classes('bg-blue-600 text-white text-sm')
    
    # Function to update displays
    async def update_displays():
        while True:
            await mock_get_stats()
            
            # Update main display values
            heading_display.set_text(f"{robot_data.heading:.2f}")
            pitch_display.set_text(f"{robot_data.pitch:.2f}")
            yaw_display.set_text(f"{robot_data.yaw:.2f}")
            angular_vel_display.set_text(f"{robot_data.angular_vel:.2f}")
            angular_accel_display.set_text(f"{robot_data.angular_accel:.2f}")
            
            # Update data grids
            position_container.clear()
            with position_container:
                create_data_grid(robot_data.positions, ['X', 'Y', 'Z'])
            
            angles_container.clear()
            with angles_container:
                create_data_grid(robot_data.angles, ['Coxa', 'Femur', 'Tibia'])
            
            offsets_container.clear()
            with offsets_container:
                create_data_grid(robot_data.offsets, ['X', 'Y', 'Z'])
            
            await asyncio.sleep(1.0)  # Update every second
    
    # Start the update loop
    asyncio.create_task(update_displays())

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title='Vega Robot Control',
        port=8080,
        host='0.0.0.0',
        reload=True,
        show=True
    )