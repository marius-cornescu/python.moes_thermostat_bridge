#!/usr/bin/env python
import pytest
import logging

import json
import re

import generic.config as config
from generic.config_logging import init_logging
from generic.json_encoders import DataClassJsonEncoder

from tinytuya.Contrib import ThermostatDevice

from moes.MoesThermostat import ThermostatState, MoesBhtThermostat


##########################################################################################################

# ***************************************************************************************
@pytest.fixture(scope="session", autouse=True)
def active_config():
    return config.ActiveConfig(app_name=__name__, config=config.DEV)


@pytest.fixture(scope="session", autouse=True)
def setup_before_any_test(active_config):
    init_logging(active_config)


@pytest.fixture
def mock_tuya_device(mocker) -> ThermostatDevice:
    mocker.patch.object(ThermostatDevice, 'sendPing', return_value=None)
    mocker.patch.object(ThermostatDevice, 'receive', return_value=None)
    mocker.patch.object(ThermostatDevice, 'status', return_value=None)
    mocker.patch.object(ThermostatDevice, 'turn_on', return_value=None)
    mocker.patch.object(ThermostatDevice, 'turn_off', return_value=None)
    mocker.patch.object(ThermostatDevice, 'set_value', return_value=None)

    return ThermostatDevice('123', '1.1.1.1', '', version=3.3)

@pytest.fixture
def moes_thermo(mock_tuya_device) -> MoesBhtThermostat:
    return MoesBhtThermostat(name="MOCK-Moes", tuya_id='123', local_ip='1.1.1.1', tuya_local_key='secret_key')


# ***************************************************************************************
@pytest.mark.parametrize('json_message, expected_object', [
    ('{}',
     '{ "is_on": null, "target_temperature": null, "home_temperature": null, "manual_operating_mode": null, "eco_mode": null, "lock_enabled": null }'),

    ('{"test": 0}',
     '{ "is_on": null, "target_temperature": null, "home_temperature": null, "manual_operating_mode": null, "eco_mode": null, "lock_enabled": null }'),

    ('{"is_on": "Some value"}',
     '{ "is_on": null, "target_temperature": null, "home_temperature": null, "manual_operating_mode": null, "eco_mode": null, "lock_enabled": null }'),

    ('{"is_on": true}',
     '{ "is_on": true, "target_temperature": null, "home_temperature": null, "manual_operating_mode": null, "eco_mode": null, "lock_enabled": null }'),

    (('{'
      '"is_on": true, '
      '"target_temperature": 20.5, '
      '"home_temperature": 19.5, '
      '"manual_operating_mode": false, '
      '"eco_mode": false, '
      '"lock_enabled": false'
      '}'),
     '{ "is_on": true, "target_temperature": 20.5, "home_temperature": 19.5, "manual_operating_mode": false, "eco_mode": false, "lock_enabled": false }'),
])
def test_mapping_json_to_test_data(json_message, expected_object):
    # given
    test_data = json.loads(json_message)

    # when
    thermostat_state = ThermostatState.from_json(test_data)

    # then
    json_text = json.dumps(thermostat_state, indent=4, cls=DataClassJsonEncoder)
    print(json_text)

    assert thermostat_state
    sanitized_json_text = json_text.replace('\n', ' ')
    sanitized_json_text = re.sub(r' +', ' ', sanitized_json_text)
    assert sanitized_json_text == expected_object

@pytest.mark.parametrize('json_message', [
    ('{}'),

    ('{"test": 0}'),

    ('{"is_on": true}'),

    (('{'
      '"is_on": true, '
      '"target_temperature": 20.5, '
      '"home_temperature": 19.5, '
      '"manual_operating_mode": false, '
      '"eco_mode": false, '
      '"lock_enabled": false'
      '}')),
])
def test_set_state(json_message, moes_thermo):
    # given
    test_data = json.loads(json_message)

    # when
    new_state = moes_thermo.set_state(ThermostatState.from_json(test_data))

    # then
    json_text = json.dumps(new_state, indent=4, cls=DataClassJsonEncoder)
    print(json_text)

    assert new_state
    sanitized_json_text = json_text.replace('\n', ' ')
    sanitized_json_text = re.sub(r' +', ' ', sanitized_json_text)
    assert sanitized_json_text



# ***************************************************************************************
