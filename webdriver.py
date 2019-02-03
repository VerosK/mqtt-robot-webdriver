from __future__ import unicode_literals, print_function

import configparser
import threading


import logging
from flask import Flask
from flask import request, render_template
from robots import RobotGroup

POOL_TIME = 5 #Seconds
APP_NAME = 'webdriver'
robot_group = None
CONFIG_FNAME = 'driver.ini'

logger = logging.getLogger('webdriver')


# global variables
backgroundThread = threading.Thread()
app = Flask(APP_NAME)

def create_app():
    global robot_group

    config = configparser.ConfigParser()
    config.read([CONFIG_FNAME])
    logging.basicConfig(level=logging.INFO)

    logger.info("Creating robot group")
    robot_group = RobotGroup(config)
    logger.info("Starting robot group")
    robot_group.run() # run in background

    logger.info("Going to start Flask app")
    return app

app = create_app()

@app.route('/')
def robot_list():
    global robot_group
    return render_template('index.html', robots=robot_group.robot_list())

@app.route('/robot/')
def catch_all():
    global robot_group
    return render_template('index.html', robots=robot_group.robot_list())

@app.route('/robot/<robot_id>/', methods=['GET', 'POST'])
def robot_page(robot_id):
    global robot_group

    if request.method == 'POST':
        data = request.form

        robot = robot_group.get_robot(robot_id)
        print(data)
        if 'left' in data and 'right' in data:
            robot.set_motors(data['left'], data['right'])
        else:
            robot.set_direction(direction=data['degree'], speed=data['distance'])

        return 'OK'
    return render_template('joystick.html')

if __name__ == '__main__':
    app.run()
