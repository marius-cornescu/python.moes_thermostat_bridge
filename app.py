#!/usr/bin/env python
import sys
import os

from bridge.bridge import Tuya2MqttBridge
from generic.config import set_active_config
from generic.config_logging import init_logging

from moes.MoesThermostat import MoesBhtThermostat
from mqtt.mqtt_server import MqttClient

##########################################################################################################



##########################################################################################################

def run_app(args):
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
