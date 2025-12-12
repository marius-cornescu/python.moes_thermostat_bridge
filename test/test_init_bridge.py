#!/usr/bin/env python
import pytest
import logging

import json
import re

import generic.config as config
from generic.config_logging import init_logging
from generic.json_encoders import DataClassJsonEncoder

from tinytuya.Contrib import ThermostatDevice


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


# ***************************************************************************************


# ***************************************************************************************
