import paho.mqtt.client as mqtt
import threading
import logging
import queue
import time
import base64
import csv
import json
import os
from tqdm import tqdm

logging.basicConfig(
    level=logging.DEBUG, 
    format='[%(asctime)s] - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MQTTRecorder')

class SslContext():

    def __init__(self, enable, ca_cert, certfile, keyfile, tls_insecure):
        self.enable = enable
        self.ca_cert = ca_cert
        self.certfile = certfile
        self.keyfile = keyfile
        self.tls_insecure = tls_insecure


class FileWriter:
    """Base class for file writers"""

    def write_message(self, row):
        """Write a message row to the file"""
        raise NotImplementedError

    def close(self):
        """Close the file"""
        raise NotImplementedError


class CsvWriter(FileWriter):

    def __init__(self, file_name):
        self.file_name = file_name
        self.file = open(file_name, 'w', newline='', buffering=1)
        self.writer = csv.writer(self.file)

    def write_message(self, row):
        self.writer.writerow(row)

    def close(self):
        self.file.close()


class JsonWriter(FileWriter):

    def __init__(self, file_name):
        self.file_name = file_name
        self.file = open(file_name, 'w', buffering=1)
        self.first_message = True
        self.file.write('[\n')

    def write_message(self, row):
        # Try to parse payload as JSON, if it fails keep it as string
        payload = row[1]
        try:
            payload = json.loads(payload)
        except (json.JSONDecodeError, TypeError):
            # Not valid JSON, keep as string
            pass

        message = {
            'topic': row[0],
            'payload': payload,
            'qos': row[2],
            'retain': row[3],
            'timestamp': row[4],
            'time_delta': row[5]
        }
        if not self.first_message:
            self.file.write(',\n')
        else:
            self.first_message = False
        json.dump(message, self.file)
        self.file.flush()

    def close(self):
        self.file.write('\n]\n')
        self.file.close()


class MqttRecorder:

    def __init__(self, host: str, port: int, client_id: str, file_name: str, username: str,
                 password: str, sslContext: SslContext, encode_b64: bool):
        self.__recording = False
        self.__messages = queue.Queue()
        self.__file_name = file_name
        self.__last_message_time = None
        self.__encode_b64 = encode_b64
        self.__file_format = self.__detect_format(file_name)
        self.__client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id)
        self.__client.on_connect = self.__on_connect
        self.__client.on_message = self.__on_message
        self.__writer_thread = None
        if username is not None:
            self.__client.username_pw_set(username, password)
        if sslContext.enable:
            self.__client.tls_set(sslContext.ca_cert, sslContext.certfile, sslContext.keyfile)
            if sslContext.tls_insecure is True:
                self.__client.tls_insecure_set(True)
        self.__client.connect(host=host, port=port)
        self.__client.loop_start()

    def __detect_format(self, file_name):
        """Detect file format based on extension"""
        _, ext = os.path.splitext(file_name)
        ext = ext.lower()
        if ext == '.json':
            return 'json'
        elif ext == '.csv':
            return 'csv'
        else:
            # Default to CSV for unknown extensions
            return 'csv'

    def __file_writer(self):
        logger.info('Saving messages to output file')
        if self.__file_format == 'json':
            writer = JsonWriter(self.__file_name)
        else:
            writer = CsvWriter(self.__file_name)

        while True:
            row = self.__messages.get()
            if not row:
                break
            writer.write_message(row)

        writer.close()

    def start_recording(self, topics: list, qos: int=0):
        self.__writer_thread = threading.Thread(target=self.__file_writer)
        self.__writer_thread.daemon = True
        self.__writer_thread.start()
        self.__last_message_time = time.time()
        if type(topics) is list and len(topics) > 0:
            for topic in topics:
                self.__client.subscribe(topic, qos=qos)
        else:
            self.__client.subscribe('#', qos=qos)
        self.__recording = True

    def start_replay(self, loop: bool):
        def decode_payload(payload, encode_b64):
            return base64.b64decode(payload) if encode_b64 else payload

        if self.__file_format == 'json':
            self.__replay_json(loop, decode_payload)
        else:
            self.__replay_csv(loop, decode_payload)

    def __replay_csv(self, loop: bool, decode_payload):
        logger.info(f"{self.__file_name}: counting lines")
        with open(self.__file_name, newline='') as csvfile:
            csv_lines = sum(1 for line in csvfile)
            logger.info(f"{self.__file_name}: {csv_lines} lines")

        with open(self.__file_name, newline='') as csvfile:
            logger.info('Starting replay')
            first_message = True
            reader = csv.reader(csvfile)
            while True:
                for row in tqdm(reader, total=csv_lines, desc='MQTT REPLAY'):
                    if not first_message:
                        time.sleep(float(row[5]))
                    else:
                        first_message = False
                    mqtt_payload = decode_payload(row[1], self.__encode_b64)
                    retain = False if row[3] == 'False' else True
                    self.__client.publish(topic=row[0], payload=mqtt_payload,
                                          qos=int(row[2]), retain=retain)
                logger.info('End of replay')
                if loop:
                    logger.info('Restarting replay')
                    time.sleep(1)
                else:
                    break

    def __replay_json(self, loop: bool, decode_payload):
        logger.info(f"{self.__file_name}: loading messages")
        with open(self.__file_name, 'r') as jsonfile:
            messages = json.load(jsonfile)
            message_count = len(messages)
            logger.info(f"{self.__file_name}: {message_count} messages")

        logger.info('Starting replay')
        while True:
            first_message = True
            for message in tqdm(messages, desc='MQTT REPLAY'):
                if not first_message:
                    time.sleep(float(message['time_delta']))
                else:
                    first_message = False

                # Handle payload: if it's a dict/list, serialize to JSON string
                payload = message['payload']
                if isinstance(payload, (dict, list)):
                    payload = json.dumps(payload)

                mqtt_payload = decode_payload(payload, self.__encode_b64)
                retain = message['retain'] if isinstance(message['retain'], bool) else message['retain'] != 'False'
                self.__client.publish(topic=message['topic'], payload=mqtt_payload,
                                      qos=int(message['qos']), retain=retain)
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
        self.__messages.put([])
        self.__writer_thread.join()


    def __on_connect(self, client, userdata, flags, rc):
        logger.info("Connected to broker!")


    def __on_message(self, client, userdata, msg):
        def encode_payload(payload, encode_b64):
            return base64.b64encode(msg.payload).decode() if encode_b64 else payload.decode()

        if self.__recording:
            logger.info("[MQTT Message received] Topic: %s QoS: %s Retain: %s",
                        msg.topic, msg.qos, msg.retain)
            time_now = time.time()
            time_delta = time_now - self.__last_message_time
            payload = encode_payload(msg.payload, self.__encode_b64)
            row = [msg.topic, payload, msg.qos, msg.retain, time_now, time_delta]
            self.__messages.put(row)
            self.__last_message_time = time_now
