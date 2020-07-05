import paho.mqtt.client as mqtt
import logging
import time
import csv
import json
from tqdm import tqdm

logging.basicConfig(
    level=logging.DEBUG, 
    format='[%(asctime)s] - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MQTTRecorder')


class MqttRecorder:

    def __init__(self, host: str, port: int, file_name: str):
        self.__recording = False
        self.__messages = list()
        self.__file_name = file_name
        self.__last_message_time = None
        self.__client = mqtt.Client()
        self.__client.on_connect = self.__on_connect
        self.__client.on_message = self.__on_message
        self.__client.connect(host=host, port=port)
        self.__client.loop_start()


    def start_recording(self, topics_file: str, qos: int=0):
        self.__last_message_time = time.time()
        if topics_file:
            with open(topics_file) as json_file:
                data = json.load(json_file)
                for topic in data['topics']:
                    self.__client.subscribe(topic, qos=qos)
        else:
            self.__client.subscribe('#', qos=qos)
        self.__recording = True


    def start_replay(self, loop: bool):
        with open(self.__file_name, newline='') as csvfile:
            logger.info('Starting replay')
            first_message = True
            reader = csv.reader(csvfile)
            messages = list(reader)
            while True:
                for row in tqdm(messages, desc='MQTT REPLAY'):
                    if not first_message:
                        time.sleep(float(row[5]))
                    else:
                        first_message = False
                    retain = False if row[3] == '0' else True
                    self.__client.publish(topic=row[0], payload=row[1],
                                          qos=int(row[2]), retain=retain)
                logger.info('End of replay')
                if loop:
                    logger.info('Restarting replay')
                    time.sleep(1)
                else:
                    break


    def stop_recording(self):
        self.__client.loop_stop()
        logger.info('Recording stopped')
        self.__recording = False
        logger.info('Saving messages to output file')
        with open(self.__file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for message in self.__messages:
                writer.writerow(message)


    def __on_connect(self, client, userdata, flags, rc):
        logger.info("Connected to broker!")


    def __on_message(self, client, userdata, msg):
        if self.__recording:
            logger.info("[MQTT Message received] Topic: %s QoS: %s Retain: %s",
                        msg.topic, msg.qos, msg.retain)
            time_now = time.time()
            time_delta = time_now - self.__last_message_time
            row = [msg.topic, msg.payload.decode(), msg.qos, msg.retain, time_now, time_delta]
            self.__messages.append(row)
            self.__last_message_time = time_now
