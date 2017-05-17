import paho.mqtt.client as mqtt
import logging
from interpolate import Interpolation

logger = logging.getLogger('robotgroup')

class RobotGroup:
    def __init__(self, config):
        self.mqtt_client = None
        self.config = config
        self.connect_mqtt()
        self._robots = {}


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

        self.mqtt_client = mqtt_client
        self.mqtt_client.message_callback_add(
                "/robot/+/$online$", self._on_online)

    def _on_online(self, client, userdata, msg):
        logging.debug('Got message: %s: %s',
                            msg.topic, msg.payload)
        parts = msg.topic.split('/')
        robot_id = parts[2]
        logging.info("Robot #%s state is %i", robot_id, int(msg.payload))
        self._robots[robot_id] = int(msg.payload)

    def run(self):
        logger.info("Starting mqtt background loop")
        self.mqtt_client.loop_start()
        logger.info("mqtt loop started")


    def robot_list(self):
        for id,online in self._robots.items():
            yield self.get_robot(id=id, online=online)

    def get_robot(self, id, online=None):
        if online is None:
            online = self._robots[id]
        return Robot(id=id,
                     mqtt_client=self.mqtt_client,
                     is_online=online)

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
    def __init__(self, id, mqtt_client, is_online=True):
        self.id = id
        self.mqtt_client = mqtt_client
        self.online = is_online

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