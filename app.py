#!/usr/bin/env python
import sys
import os

import argparse

from bridge.bridge import Tuya2MqttBridge
from generic.config import set_active_config
from generic.config_logging import init_logging

from moes.MoesThermostat import MoesBhtThermostat
from mqtt.mqtt_server import MqttClient

##########################################################################################################

##########################################################################################################

def run_app(args: argparse.Namespace):
    active_config = set_active_config(args.target_env, args.app_name)
    logging = init_logging(active_config)

    logging.info(f'\n{log_startup_data(args)}\n')
    logging.info('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    logging.info('>> START: TUYA SERVICE: Setup >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')

    thermostat = MoesBhtThermostat(name=args.tuya_dev_name,
                                   tuya_id=args.tuya_dev_id, local_ip=args.tuya_dev_ip,
                                   tuya_local_key=args.tuya_dev_local_key)

    logging.info('')
    logging.info('<< END: TUYA SERVICE: Setup <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    logging.info('>> START: Mqtt SERVICE: Setup >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')

    mqtt_client = MqttClient(name=args.mqtt_broker_name,
                             broker_address=args.mqtt_broker_addr, broker_port=args.mqtt_broker_port,
                             username=args.mqtt_user, password=args.mqtt_password,
                             tls_cert_path=args.mqtt_tls_path,
                             topic_root=f'home/hvac/thermostat/{thermostat.name}')

    logging.info('')
    logging.info('<< END: Mqtt SERVICE: Setup <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    logging.info('>> START: BRIDGE >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')

    bridge = Tuya2MqttBridge(tuya_device=thermostat, mqtt_client=mqtt_client)
    bridge.start()

    logging.info('')
    logging.info('<< END: BRIDGE <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    logging.info('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')

##########################################################################################################

def log_startup_data(args: argparse.Namespace):
    return (
        '=================================================================\n'
        f'TUYA: [{args.tuya_dev_name}]:\n'
        f' * id = [{args.tuya_dev_id}] / ip = [{args.tuya_dev_ip}]\n'
        f'<<<<<<--------------------------------------->>>>>>\n'
        f'MQTT: [{args.mqtt_broker_name}]:\n'
        f' * addr = [{args.mqtt_broker_addr}]:[{args.mqtt_broker_port}]\n'
        f' * user = [{args.mqtt_user}]\n'
        '=================================================================\n'
    )

##########################################################################################################
