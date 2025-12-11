#!/usr/bin/env python
import sys
import os

import argparse
import datetime

import app
from generic import setup_cleanup_on_exit, callback_on_exit


##########################################################################################################


def main():
    parser = argparse.ArgumentParser(
        description='Call local tuya device')

    parser.add_argument(
        '--target_env', metavar='target_env', type=str,
        help='target environment (TEST/PROD)')

    parser.add_argument('--tuya_dev_id', type=str, required=True,
                        help='Tuya: device id')

    parser.add_argument('--tuya_dev_ip', type=str, required=True,
                        help='Tuya: device ip address')

    parser.add_argument('--tuya_dev_local_key', type=str, required=True,
                        help='Tuya: device local key')

    parser.add_argument('--mqtt_broker_addr', type=str, required=True,
                        help='Mqtt: server address')

    parser.add_argument('--mqtt_broker_port', type=int, default=8883,
                        help='Mqtt: server port')

    parser.add_argument('--mqtt_user', type=str, required=True,
                        help='Mqtt: server user name')
    parser.add_argument('--mqtt_password', type=str, required=True,
                        help='Mqtt: server password')

    parser.add_argument('--mqtt_tls_path', type=str, required=False,
                        help='Mqtt: Path to the tls certificate used by the server')

    parser.add_argument("--static_data", nargs='?', type=bool,
                        const=True, default=False)

    args = parser.parse_args()

    args.app_name = os.path.splitext(os.path.basename(__file__))[0]
    args.tuya_dev_name="BHT-002-GALW"
    args.mqtt_broker_name="MQTT"
    args.mqtt_topic_root=f'home/hvac/thermostat/{args.tuya_dev_name}'

    app.run_app(args)


##########################################################################################################

if __name__ == '__main__':
    start_time = datetime.datetime.now()
    sys.__stdout__.write('%s \n' % start_time.ctime())
    sys.__stdout__.flush()

    try:
        setup_cleanup_on_exit()
        main()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("KeyboardInterrupt received, exiting...")
        callback_on_exit()

    end_time = datetime.datetime.now()
    sys.__stdout__.write('%s \n' % end_time.ctime())
    sys.__stdout__.write('TOTAL DURATION = %s \n' % (end_time - start_time))
    sys.__stdout__.flush()
