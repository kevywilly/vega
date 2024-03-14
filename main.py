import logging
import time
import os
from flask_cors import CORS
from flask import Flask, Response, request

from src.interfaces.vector import Pos3d
from src.nodes.robot import Robot
from settings import settings

from config import Positions
from src.nodes.robot import Robot

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

OK = {"status": "ok"}

app = Flask(__name__)
robot = Robot()
app.robot = robot

CORS(app, resource={
    r"/*": {
        "origins": "*"
    }
})


def demo():
    positions = [Positions.ready, Positions.crouch, Positions.ready]

    for p in positions:
        robot.set_targets(p)
        robot.move_to_targets()
        robot.print_stats()
        time.sleep(2)

    """
    command {11: 491, 12: 500, 13: 375, 21: 508, 22: 500, 23: 625, 31: 508, 32: 500, 33: 625, 41: 491, 42: 500, 43: 375}
    ready {11: 491, 12: 315, 13: 720, 21: 508, 22: 684, 23: 279, 31: 508, 32: 684, 33: 279, 41: 491, 42: 315, 43: 720}
    crouch {11: 491, 12: 166, 13: 966, 21: 508, 22: 833, 23: 33, 31: 508, 32: 833, 33: 33, 41: 491, 42: 166, 43: 966}
    """

@app.get('/')
def _index():
    return OK

@app.get('/demo')
def _demo():
    demo()
    return OK

@app.post('/target')
def _target():
    data = request.get_json()
    pos = Pos3d(**data)
    return data

if __name__ == "__main__":
    app.robot.spin(frequency=50)
    app.run(host='0.0.0.0', debug=False)