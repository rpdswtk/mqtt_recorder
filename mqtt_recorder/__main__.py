from mqtt_recorder.recorder import MqttRecorder
import argparse
import time

parser = argparse.ArgumentParser(
    prog='mqtt_recorder',
    description="Tool for recording and replaying mqtt messages"
)

parser.add_argument(
    '--host',
    type=str,
    required=True,
    help='MQTT broker address'
)

parser.add_argument(
    '--port',
    type=int,
    default=1883,
    help='MQTT broker port'
)

parser.add_argument(
    '--mode',
    type=str,
    help='mode: record/replay',
    required=True
)

parser.add_argument(
    '--file',
    type=str,
    help='output/input file',
    required=True
)

parser.add_argument(
    '--loop',
    type=bool,
    help='looping replay',
    default=False
)

parser.add_argument(
    '--qos',
    type=int,
    help='Quality of Service that will be used for subscriptions',
    default=0
)

parser.add_argument(
    '--topics',
    type=str,
    help='json file containing selected topics for subscriptions'
)


def wait_for_keyboard_interrupt():
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        pass


def main():
    args = parser.parse_args()
    recorder = MqttRecorder(args.host, args.port, args.file)
    if args.mode == 'record':
        recorder.start_recording(qos=args.qos, topics_file=args.topics)
        wait_for_keyboard_interrupt()
        recorder.stop_recording()
    elif args.mode == 'replay':
        try:
            recorder.start_replay(args.loop)
        except KeyboardInterrupt:
            pass
    else:
        print('Please select a mode record/replay')


if __name__ == "__main__":
    main()
