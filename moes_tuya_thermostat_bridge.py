#!/usr/bin/env python
import sys
import os

import argparse
import datetime

from bridge.bridge import Tuya2MqttBridge
from generic import setup_cleanup_on_exit, callback_on_exit
from generic.config import set_active_config
from generic.config_logging import init_logging

from moes.MoesThermostat import MoesBhtThermostat
from mqtt.mqtt_server import MqttClient


##########################################################################################################


def main():
    parser = argparse.ArgumentParser(
        description='Call local tuya device')

    parser.add_argument(
        '--target_env', metavar='target_env', type=str,
        help='target environment (TEST/PROD)')

    parser.add_argument('--tuya_dev_id', type=str,
                        help='Tuya: device id')

    parser.add_argument('--tuya_dev_ip', type=str,
                        help='Tuya: device ip address')

    parser.add_argument('--tuya_dev_local_key', type=str,
                        help='Tuya: device local key')

    parser.add_argument('--mqtt_broker_addr', type=str,
                        help='Mqtt: server address')

    parser.add_argument('--mqtt_broker_port', type=int, default=8883,
                        help='Mqtt: server port')

    parser.add_argument('--mqtt_user', type=str,
                        help='Mqtt: server user name')
    parser.add_argument('--mqtt_password', type=str,
                        help='Mqtt: server password')

    parser.add_argument('--mqtt_tls_path', type=str,
                        help='Mqtt: Path to the tls certificate used by the server')

    parser.add_argument("--static_data", nargs='?', type=bool,
                        const=True, default=False)

    args = parser.parse_args()

    active_config = set_active_config(args.target_env, get_app_name())
    logging = init_logging(active_config)

    logging.info('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    logging.info('>> TUYA SERVICE >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')

    thermostat = MoesBhtThermostat(name="BHT-002-GALW", tuya_id=args.tuya_dev_id, local_ip=args.tuya_dev_ip,
                                   tuya_local_key=args.tuya_dev_local_key)

    logging.info('')
    logging.info('<< TUYA SERVICE <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    logging.info('>> Mqtt SERVICE >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')

    mqtt_client = MqttClient(name='Mqtt',
                             broker_address=args.mqtt_broker_addr, broker_port=args.mqtt_broker_port,
                             username=args.mqtt_user, password=args.mqtt_password,
                             tls_cert_path=args.mqtt_tls_path,
                             topic_root=f'home/hvac/thermostat/{thermostat.name}')

    logging.info('')
    logging.info('<< Mqtt SERVICE <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    logging.info('>> BRIDGE >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')

    bridge = Tuya2MqttBridge(tuya_device=thermostat, mqtt_client=mqtt_client)
    bridge.start()

    logging.info('')
    logging.info('<< BRIDGE <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    logging.info('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')

##########################################################################################################

def get_app_name():
    return os.path.splitext(os.path.basename(__file__))[0]

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
