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
    help=' MQTT broker address'
)

parser.add_argument(
    '--port',
    type=int,
    default=1883,
    help=' MQTT broker port'
)

parser.add_argument(
    '--mode',
    type=str,
    required=True,
    help='mode: record/replay'
)

parser.add_argument(
    '--file',
    type=str,
    help='output/input file',
    required=True
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
        recorder.start_recording()
        wait_for_keyboard_interrupt()
        recorder.stop_recording()
    elif args.mode == 'replay':
        try:
            recorder.start_replay()
        except KeyboardInterrupt:
            pass
    else:
        print('Please select a mode record/replay')


if __name__ == "__main__":
    main()
