from __future__ import unicode_literals

import paho.mqtt.client as mqtt
import logging
from interpolate import Interpolation
from datetime import datetime, timedelta

logger = logging.getLogger('robotgroup')

class RobotGroup:
    def __init__(self, config):
        self.mqtt_client = None
        self.config = config
        self.connect_mqtt()
        self._robots = {} # robot names
        self._last_seen = {}  # datetime or None


    def connect_mqtt(self):
        mqtt_config = self.config['mqtt-server']
        #
        mqtt_client = mqtt.Client()
        if 'username' in mqtt_config:
            mqtt_client.username_pw_set(mqtt_config['username'],
                                        mqtt_config['password'])
        mqtt_client.connect(host=mqtt_config['host'])
        logger.info("MQTT connecting to %s", mqtt_config['host'])
        mqtt_client.subscribe('/robot/+/$online$')
        mqtt_client.subscribe('/robot/+/$name$')

        self.mqtt_client = mqtt_client
        self.mqtt_client.message_callback_add(
                "/robot/+/$online$", self._on_online)
        self.mqtt_client.message_callback_add(
                "/robot/+/$name$", self._on_name)

    def _on_name(self, client, userdata, msg):
        logging.debug('Got name message: %s: %s',
                            msg.topic, msg.payload)
        parts = msg.topic.split('/')
        robot_id = parts[2]
        logging.info("Robot #%s name is %s", robot_id, repr(msg.payload))
        try:
            self._robots[robot_id] = msg.payload.decode('us-ascii')
        except UnicodeDecodeError:
            self._robots[robot_id] = 'WFT'


    def _on_online(self, client, userdata, msg):
        logging.debug('Got alive message: %s: %s',
                            msg.topic, msg.payload)
        parts = msg.topic.split('/')
        robot_id = parts[2]
        logging.info("Robot #%s state is %i", robot_id, int(msg.payload))
        if int(msg.payload) == 0:
            self._last_seen[robot_id] = None
        else:
            self._last_seen[robot_id] = datetime.now()

    def run(self):
        logger.info("Starting mqtt background loop")
        self.mqtt_client.loop_start()
        logger.info("mqtt loop started")


    def robot_list(self):
        for id in sorted(self._last_seen):
            yield self.get_robot(id=id)

    def get_robot(self, id, online=None):
        if online is None:
            online = self._last_seen[id]
        return Robot(id=id,
                     mqtt_client=self.mqtt_client,
                     is_online=online,
                     name=self._robots.get(id, None),
                     last_seen=self._last_seen[id])

# inspired by http://stackoverflow.com/a/17115473/7554925

class SpeedTable:
    DATA = [
        dict(angle=  0, left=+1, right=+1),
        dict(angle= 45, left=+1, right= 0),
        dict(angle= 90, left=+1, right=-1),
        dict(angle=135, left= 0, right=-1),
        dict(angle=180, left=-1, right=-1),
        dict(angle=225, left=-1, right= 0),
        dict(angle=270, left=-1, right=+1),
        dict(angle=315, left= 0, right=+1),
        dict(angle=360, left=+1, right=+1),
    ]
    ANGLES = [i['angle'] for i in DATA]
    LEFT   = [i['left']  for i in DATA]
    RIGHT  = [i['right'] for i in DATA]

    print(LEFT)

    left_interpolation = Interpolation(x_list=ANGLES, y_list=LEFT)
    right_interpolation = Interpolation(x_list=ANGLES, y_list=RIGHT)

    @classmethod
    def from_angle(cls, angle, speed):
        left = cls.left_interpolation[angle] * speed
        right = cls.right_interpolation[angle] * speed
        return dict(left=left, right=right)

class Robot:
    def __init__(self, id, mqtt_client, is_online=True, name=None, last_seen=None):
        self.id = id
        self.mqtt_client = mqtt_client
        self.online = is_online
        self.last_seen = last_seen
        self.name = name or 'Unnamed'

    @property
    def last_seen_str(self):
        if not self.last_seen:
            return 'disconnected'
        delta = datetime.now() - self.last_seen
        print(self.last_seen, delta)
        if delta < timedelta(seconds=60):
            return 'alive'
        if delta < timedelta(minutes=30):
            return 'before {} minutes'.format(delta.seconds // 60)
        return 'disconnected (probably)'

    @property
    def alive_color(self):
        if not self.last_seen:
            return '#FFFFFF'
        delta = datetime.now() - self.last_seen
        print(self.last_seen, delta)
        if delta < timedelta(seconds=60):
            return '#20FF20'
        if delta < timedelta(minutes=30):
            return '#008000'
        return '#ffffff'

    def set_direction(self, direction, speed):
        """
        Send motors to robot
        
        :param direction:   joystick direction in degrees 
        :param speed:  speed from 0 to 100
        :return: 
        """
        # drop pi/4
        direction = float(direction)
        speeds = SpeedTable.from_angle(
            angle=direction, speed=float(speed))
        self.set_motors(**speeds)

    def set_motors(self, left, right):
        left,right = int(left),int(right)
        logger.info("left=%s right=%s", left, right)
        self.mqtt_client.publish(
            "/robot/{}/motors".format(self.id),
            '{},{}'.format(left, right))
