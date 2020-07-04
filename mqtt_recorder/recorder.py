import paho.mqtt.client as mqtt
import logging
import time
import csv
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


    def start_recording(self, topics: list=[]):
        self.__last_message_time = time.time()
        if len(topics) == 0:
            self.__client.subscribe('#')
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
                        time.sleep(float(row[3]))
                    else:
                        first_message = False
                    self.__client.publish(topic=row[0], payload=row[1])
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
            logger.info("[MQTT Message received] Topic: %s Payload: %s",
                        msg.topic, msg.payload.decode())
            time_now = time.time()
            time_delta = time_now - self.__last_message_time
            row = [msg.topic, msg.payload.decode(), time_now, time_delta]
            self.__messages.append(row)
            self.__last_message_time = time_now
