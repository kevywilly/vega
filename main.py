#!/usr/bin/python3

import logging
import os
import time

import numpy as np
from flask import Flask, Response, request, render_template
from flask_cors import CORS

from settings import settings
from src.model.types import MoveTypes
from src.nodes.robot import Robot

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

OK = {"status": "ok"}

app = Flask(__name__)

CORS(app, resource={
    r"/*": {
        "origins": "*"
    }
})


def get_stats():

    heading, pitch, yaw = app.robot.imu.euler
    voltage = app.robot.controller.voltage()
    pose = app.robot.controller.pose
    return {
        "heading": heading,
        "pitch": pitch,
        "yaw": yaw,
        "voltage": voltage,
        "angles": pose.angles_in_degrees.tolist(),
        "positions": pose.positions.astype(int).tolist(),
        "offsets": settings.position_offsets.astype(int).tolist(),
        "tilt": settings.tilt.json(),
        "height": pose.height,
        "height_pct": app.robot.controller.pose.height_pct,
    }


@app.get('/')
def _index():
    return render_template('index.html')


@app.get('/healthcheck')
def _health_check():
    return OK


@app.get('/api/demo')
def _demo():
    app.robot.demo()
    return OK


@app.post('/api/target')
def _target():
    data = request.get_json()
    return data


@app.post('/api/move/<move_type>')
def _move(move_type: MoveTypes):
    return app.robot.process_move(move_type)


@app.get('/api/stream')
def stream():
    return Response(app.robot.get_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.get('/api/stats')
def stats():
    return get_stats()


@app.get('/api/targets')
def _get_targets():
    return app.robot.controller.pose.target_positions.tolist()


@app.post('/api/pose/<value>')
def _set_pose(value: str):
    v = value.lower()

    p = None

    if v == "ready":
        p = settings.position_ready
    elif v == "sit":
        p = settings.position_sit
    elif v == "crouch":
        p = settings.position_crouch
    else:
        return {"status": "error, unknown pose"}

    if app.robot.walking:
        app.robot.stop()
        time.sleep(0.5)

    app.robot.set_targets(p)
    app.robot.move_to_targets()

    return {"status": "ok"}


@app.post('/api/tilt/<type>/<degrees>')
def _set_tilt(type: str, degrees: int):
    if type == "yaw":
        settings.tilt.yaw = int(degrees)
    elif type == "pitch":
        settings.tilt.pitch = int(degrees)

    return settings.tilt.json()

@app.get('/api/tilt')
def _get_tilt():
    return settings.tilt.json()

@app.post('/api/targets')
def _set_targets():
    data = request.get_json()
    if not data:
        app.robot.set_targets(settings.position_ready)
    else:
        app.robot.set_targets(np.array(data).astype(np.int16))

    app.robot.move_to_targets()

    return app.robot.controller.pose.target_positions.tolist()


@app.get('/api/offsets')
def ready():
    return settings.position_offsets.tolist()

@app.post('/api/level')
def level():
    app.robot.level()
    return settings.position_offsets.tolist()

@app.post('/api/offsets')
def post_ready():
    data = request.get_json()
    if not data:
        settings.reset_offsets()
    else:
        settings.position_offsets = np.array(data).astype(int)

    return settings.position_offsets.tolist()


@app.get('/api/stop')
def stop():
    app.robot.stop()
    return {"status": "stopped"}


if __name__ == "__main__":
    app.robot = Robot()
    app.robot.spin(frequency=50)
    app.run(host='0.0.0.0', debug=settings.environment == "development")
