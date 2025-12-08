#!/usr/bin/env python
from typing import Any, Final, Optional, Dict
import logging
from dataclasses import dataclass

import threading

from paho.mqtt.enums import MQTTErrorCode
import paho.mqtt.client as mqtt

from bridge import MqttCallbackOnMessage

##########################################################################################################

# MQTT broker details
# BROKER = "mqtt.example.com"  # Replace with your broker's address
# PORT = 8883  # Default port for MQTT over TLS
# USERNAME = "your_username"
# PASSWORD = "your_password"
# TOPIC_SUBSCRIBE = "example/topic"  # Topic to listen to
# TOPIC_PUBLISH = "example/topic"  # Topic to send messages to
# TLS_CERT_PATH = "/path/to/ca.crt"  # Path to your CA certificate file

##########################################################################################################

@dataclass
class MqttClient(object):
    name: str

    broker_address: str
    broker_port: int

    client: Final[mqtt.Client]

    topic_root: Final[str]

    def __init__(self, name:str, broker_address:str, broker_port: int, username: str, password: str, tls_cert_path:str, topic_root: str = 'home/tuya2mqtt_bridge',
                 client: mqtt.Client | None = None):
        self.name = name

        self.is_connected = False

        self.broker_address = broker_address
        self.broker_port = broker_port

        if client is None:
            client = self.__setup_client(username, password, tls_cert_path)
        self.client = client

        # Attach callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        self.topic_root = topic_root

        self._callback_mutex = threading.RLock()
        self._on_callback: MqttCallbackOnMessage | None = None

    def __setup_client(self, username: str, password: str, tls_cert_path:str) -> mqtt.Client:
        logging.getLogger(__name__).debug(f'Setup mqtt client [{self.name}]')
        # Create an MQTT client instance
        client = mqtt.Client()

        # Set username and password
        client.username_pw_set(username, password)

        # Enable TLS
        client.tls_set(tls_cert_path)

        return client

    def connect(self):
        logging.getLogger(__name__).debug(f'Connecting to [{self.name}] on [{self.broker_address}:{self.broker_port}]')
        # Connect to the broker
        response = self.client.connect(self.broker_address, self.broker_port)
        self.is_connected = (response == MQTTErrorCode.MQTT_ERR_SUCCESS)

        if self.is_connected:
            logging.getLogger(__name__).info(f'Successfully connected to [{self.name}] on [{self.broker_address}:{self.broker_port}]')
        else:
            logging.getLogger(__name__).error(f'Failed to connect [{self.name}] on [{self.broker_address}:{self.broker_port}] | response code [{response}]')

    def loop_start(self):
        logging.getLogger(__name__).info(f'Starting [{self.name}] listening loop.')

        if not self.is_connected:
            self.connect()

        # Start the network listening loop in a separate thread
        self.client.loop_start()

    def loop_stop(self):
        logging.getLogger(__name__).info(f'Stopping [{self.name}] listening loop.')

        self.client.loop_stop()
        self.client.disconnect()
        self.is_connected = False

    def publish(self, topic: str, payload: str):
        logging.getLogger(__name__).debug(f'Publishing to [{self.name}] message [{payload}] on topic [{topic}].')

        if not self.is_connected:
            self.connect()

        if self.is_connected:
            self.client.publish(topic, payload)
            logging.getLogger(__name__).debug(f'Published to [{self.name}] message [{payload}] on topic [{topic}].')


    # Callback when the client connects to the broker
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.getLogger(__name__).debug(f"Connected to [{self.name}] successfully!")
            # Subscribe to a topic
            client.subscribe(self.topic_listen)
            logging.getLogger(__name__).debug(f"Subscribed to topic: [{self.topic_listen}]")
        else:
            logging.getLogger(__name__).debug(f"Connection to [{self.name}] failed with code [{rc}]")

    # Callback when a message is received
    def _on_message(self, client, userdata, msg):
        logging.getLogger(__name__).debug(f"Received from [{self.name}] message [{msg.payload.decode()}] on topic [{msg.topic}]")

    @property
    def topic_root(self) -> str:
        return self._topic_root

    @topic_root.setter
    def topic_root(self, topic_root: str | None) -> None:
        logging.getLogger(__name__).info(f'Set topic_root [{topic_root}]')

        if topic_root:
            self._topic_root = topic_root
            self.topic_lwt = f'{self._topic_root}/LWT'
            self.topic_status = f'{self._topic_root}/STATE'
            self.topic_listen = f'{self._topic_root}/COMMAND'

        logging.getLogger(__name__).debug(f'topic_lwt=[{self.topic_lwt}] / topic_status=[{self.topic_status}] / topic_listen=[{self.topic_listen}]')

    @property
    def on_callback(self) -> MqttCallbackOnMessage | None:
        """The callback called when the tuya device gets updates.
        """
        return self._on_callback

    @on_callback.setter
    def on_callback(self, func: MqttCallbackOnMessage | None) -> None:
        with self._callback_mutex:
            self._on_callback = func

