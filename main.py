# !/usr/bin/python3i

import logging
import os
import time
import uvicorn
from flask import Flask, Response, request, render_template
from flask_cors import CORS
from robolib.interfaces.vector import Pos3d
from robolib.settings import settings

from vega.nodes.robot import Robot

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
    positions = [settings.quadruped.position_ready, settings.quadruped.position_crouch,
                 settings.quadruped.position_ready]

    for p in positions:
        app.robot.set_targets(p)
        app.robot.move_to_targets()
        app.robot.print_stats()
        time.sleep(2)

    """
    command {11: 491, 12: 500, 13: 375, 21: 508, 22: 500, 23: 625, 31: 508, 32: 500, 33: 625, 41: 491, 42: 500, 43: 375}
    ready {11: 491, 12: 315, 13: 720, 21: 508, 22: 684, 23: 279, 31: 508, 32: 684, 33: 279, 41: 491, 42: 315, 43: 720}
    crouch {11: 491, 12: 166, 13: 966, 21: 508, 22: 833, 23: 33, 31: 508, 32: 833, 33: 33, 41: 491, 42: 166, 43: 966}
    """


@app.get('/')
def _index():
    message = "Hello, World"
    return render_template('index.html',
                           message=message)


@app.get('/health')
def health():
    return OK


@app.get('/api/demo')
def _demo():
    demo()
    return OK


@app.post('/api/target')
def _target():
    data = request.get_json()
    pos = Pos3d(**data)
    return data


@app.post('/api/joy/<id>')
def _joy(id: str):
    data = request.get_json()
    data["id"] = int(id)
    return data


@app.get('/api/stream')
def stream():
    return Response(app.robot.get_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.get('/api/stats')
def stats():
    heading, pitch, yaw = app.robot.imu.euler
    voltage = app.robot.controller.voltage()
    return {
        "stats": {
            "heading": heading,
            "pitch": pitch,
            "yaw": yaw,
            "voltage": voltage
        }
    }


@app.get('/api/config')
def config():
    return settings.dict()


if __name__ == "__main__":
    #uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
    app.robot = Robot()
    app.robot.spin(frequency=50)
    app.run(host='0.0.0.0', debug=False)
