# !/usr/bin/python3i

import logging
import os
import time

from flask import Flask, Response, request, render_template
from flask_cors import CORS
import numpy as np

import config
from config import POSITIONS
from src.motion.gaits.sidestep import Sidestep
from src.motion.gaits.trot import Trot
from src.motion.gaits.turn import Turn
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


def demo():
    positions = [POSITIONS.READY, POSITIONS.CROUCH, POSITIONS.READY]

    for p in positions:
        app.robot.set_targets(p)
        app.robot.move_to_targets()
        time.sleep(2)

    """
    command {11: 491, 12: 500, 13: 375, 21: 508, 22: 500, 23: 625, 31: 508, 32: 500, 33: 625, 41: 491, 42: 500, 43: 375}
    ready {11: 491, 12: 315, 13: 720, 21: 508, 22: 684, 23: 279, 31: 508, 32: 684, 33: 279, 41: 491, 42: 315, 43: 720}
    crouch {11: 491, 12: 166, 13: 966, 21: 508, 22: 833, 23: 33, 31: 508, 32: 833, 33: 33, 41: 491, 42: 166, 43: 966}
    """


@app.get('/')
def _index():
    return render_template('index.html', vega_api_url=config.VEGA_API_URL)


@app.get('/healthcheck')
def _health_check():
    return OK


@app.get('/api/demo')
def _demo():
    demo()
    return OK


@app.post('/api/target')
def _target():
    data = request.get_json()
    return data


@app.post('/api/move')
def _move():
    data = request.get_json()
    return data


@app.post('/api/joy')
def _joy():
    data = request.get_json()
    return app.robot.process_joy(data)


@app.get('/api/stream')
def stream():
    return Response(app.robot.get_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.get('/api/stats')
def stats():
    heading, pitch, yaw = app.robot.imu.euler
    voltage = app.robot.controller.voltage()
    return {
        "heading": heading,
        "pitch": pitch,
        "yaw": yaw,
        "voltage": voltage
    }

@app.get('/api/offsets')
def ready():
    return config.POSITIONS.OFFSETS.tolist()


@app.post('/api/offsets')
def post_ready():
    data = request.get_json()
    if not data:
        config.POSITIONS.reset()
    else:
        config.POSITIONS.OFFSETS = np.array(data).astype(np.int16)

    return config.POSITIONS.OFFSETS.tolist()


@app.get('/api/stop')
def stop():
    app.robot.stop()
    return {"status": "stopped"}


if __name__ == "__main__":
    app.robot = Robot()
    app.robot.spin(frequency=50)
    app.run(host='0.0.0.0', debug=config.VEGA_ENVIRONMENT == "development")
