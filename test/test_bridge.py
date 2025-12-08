#!/usr/bin/env python
import pytest
import logging

import json

import paho.mqtt.client as mqtt
from tinytuya.Contrib import ThermostatDevice

import generic.config as config
from bridge.bridge import Tuya2MqttBridge
from generic.config_logging import init_logging
from moes.MoesThermostat import MoesBhtThermostat
from mqtt.client import MqttClient


##########################################################################################################

# ***************************************************************************************
@pytest.fixture(scope="session", autouse=True)
def active_config():
    return config.ActiveConfig(app_name=__name__, config=config.DEV)

@pytest.fixture(scope="session", autouse=True)
def setup_before_any_test(active_config):
    init_logging(active_config)

@pytest.fixture
def mock_tuya_device() -> ThermostatDevice:
    # FIXME: return a mock version of the object
    return None

@pytest.fixture
def moes_thermo(mock_tuya_device) -> MoesBhtThermostat:
    return MoesBhtThermostat(name="MOCK-Moes", tuya_id='123', local_ip='1.1.1.1', tuya_local_key='secret_key')

@pytest.fixture
def mock_mqtt_client() -> mqtt.Client:
    # FIXME: return a mock version of the object
    return None

@pytest.fixture
def mqtt_service(mock_mqtt_client, moes_thermo) -> MqttClient:
    return MqttClient(name='Mqtt', broker_address='broker_address', broker_port=1234,
                      username="mqtt_user", password="mqtt_password",
                      tls_cert_path="mqtt_tls_path",
                      topic_root=f'home/hvac/thermostat/{moes_thermo.name}',
                      client=mock_mqtt_client)


# ***************************************************************************************
def test_bridge_get_access_token(moes_thermo, mqtt_service):
    # given
    bridge = Tuya2MqttBridge(tuya_device=moes_thermo, mqtt_client=mqtt_service)

    # when
    _ = bridge.start()

    # then
    assert True


@pytest.mark.skip(reason="Real test")
def test_bridge():
    # given
    bridge = Tuya2MqttBridge(tuya_device=None, mqtt_client=None)

    # when
    _ = bridge.start()

    # then
    assert True

@pytest.mark.parametrize('api_response_file_name, plugin_name', [
    ('resources/sample_test_response.json', ''),
])
def test_mapping_json_to_test_data(api_response_file_name, plugin_name):
    # given
    with open(api_response_file_name, 'r') as test_data:
        endpoint_data_content = test_data.read()

    test_data = json.loads(endpoint_data_content)

    # when
    # use data

    # then
    json_text = json.dumps(test_data, indent=4)
    print(json_text)

    assert test_data

# ***************************************************************************************
