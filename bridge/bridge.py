#!/usr/bin/env python
from typing import Any, Final, Optional, Dict
import logging
from dataclasses import dataclass

from generic import register_on_exit_action
from moes.MoesThermostat import MoesBhtThermostat
from mqtt.mqtt_server import MqttClient

##########################################################################################################

# Scenarios:
# message on mqtt -> mqtt_client gets message -> analyse message -> call specific method on tuya_device
# tuya_device is connected -> getting all values -> convert to json -> publish mqtt message with mqtt_client to STATUS topic
# tuya_device is updated -> convert to json -> publish mqtt message with mqtt_client to UPDATE topic (and/or UPDATE/parameter - one topic per parameter)
#
# tasmota topics:
# LWT       = Online / Offline
# STATE     = json with the entire state
#

##########################################################################################################

@dataclass
class Tuya2MqttBridge(object):
    tuya_device: Final[MoesBhtThermostat]
    mqtt_client: Final[MqttClient]

    def start(self, max_iterations: int = 0):
        logging.getLogger(__name__).debug(f'Start Tuya[{self.tuya_device.name}] <=> Mqtt[{self.mqtt_client.name}] bridge')

        self.tuya_device.on_callback = self.from_tuya_callback
        self.mqtt_client.on_callback = self.from_mqtt_callback

        register_on_exit_action(lambda: self.mqtt_client.loop_stop())
        self.mqtt_client.loop_start()

        self.tuya_device.connect()
        self.tuya_device.start_monitoring(max_iterations=max_iterations)
        # Tuya monitoring uses the main thread

    def to_tuya_callback(self, user_data: Any, data: Dict[str, Any]):
        logging.getLogger(__name__).warning(f'Received action for Tuya device [{self.tuya_device.name}] data=[{data}]')

        # FIXME: verify with the synced state and if update required, call specific method on tuya device

    def from_tuya_callback(self, user_data: Any, data: Dict[str, Any]):
        logging.getLogger(__name__).warning(f'Received action from Tuya device [{self.tuya_device.name}] data=[{data}]')

        self.mqtt_client.publish_state(data)

        # FIXME: call publish to mqtt topic

    def to_mqtt_callback(self, user_data: Any, data: Dict[str, Any]):
        logging.getLogger(__name__).warning(f'Received action for Mqtt service [{self.mqtt_client.name}] data=[{data}]')
        # FIXME: ??

    def from_mqtt_callback(self, user_data: Any, data: Dict[str, Any]):
        logging.getLogger(__name__).warning(f'Received action from Mqtt service [{self.mqtt_client.name}] data=[{data}]')

        if 'manual_operating_mode' in data:
            new_mode = data['manual_operating_mode'] == True
            self.tuya_device.set_manual_operating_mode(new_mode)

        # FIXME: ??
