# webdriver

How to start:

 * set-up mqtt broker (or use public)

 * connect your robot to the MQTT broker

 * add MQTT broker to your page

 * Run `main.py`

 * Use joystick on http://127.0.0.1:5000/


Micropython part is available on https://github.com/VerosK/mqtt-robot-nodemcu

## `curl` shortcut 

    curl http://127.0.0.1:5000/robot/178c2300/ -X POST --form left=100 --form right=100