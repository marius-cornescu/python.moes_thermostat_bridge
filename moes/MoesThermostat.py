#!/usr/bin/env python
from typing import Any, Final, Optional, Dict
import logging
from dataclasses import dataclass

import time
import threading

from tinytuya import Contrib

from bridge import TuyaCallbackOnAction

##########################################################################################################

#'dps': {'1': True, '2': 40, '3': 40, '4': '0', '5': False, '6': False, '102': 0, '104': True}
#       {'1': True, '2': 46, '3': 41, '4': '0', '5': False, '6': False, '102': 0, '104': True}
# '1': True     = Power mode = ON / OFF
# '2': 40,      = Temperature =
#           60 = 30 grade
#           50 = 25 grade
#           40 = 20 grade
#           30 = 15 grade
#           20 = 10 grade
#           10 = 5 grade
# '3': 40,      = ?? actual temperature ??
# '4': '0',     = mode manual / automatic = value is string = '0' for automatic / '1' for manual
# '5': False,   = Eco mode = ON / OFF
# '6': False,   = Lock = ON / OFF
# '102': 0,     = ??  ??
# '104': True   = ??  ??

MOES_POWER_STATUS = 1
MOES_TARGET_TEMPERATURE = 2
MOES_MEASURED_TEMPERATURE = 3
MOES_OPERATING_MODE = 4
MOES_ECO_MODE_ENABLED = 5
MOES_LOCK_ENABLED = 6

MOES_TEMPERATURE_SCALE = 2


##########################################################################################################

@dataclass
class MoesBhtThermostat(object):
    name: str
    tuya_id: str
    local_ip: str
    tuya_local_key: str

    device: Final[Contrib.ThermostatDevice]

    is_synchronized: Optional[bool] = False

    is_on: bool = False
    target_temperature: float = 0.0
    home_temperature: float = 0.0
    manual_operating_mode: int = 0
    eco_mode: bool = False
    lock_enabled: Optional[bool] = None

    ping_time: Optional[float] = None

    def __init__(self, name:str, tuya_id:str, local_ip:str, tuya_local_key:str):
        self.name = name
        self.tuya_id = tuya_id
        self.local_ip = local_ip
        self.tuya_local_key = tuya_local_key

        self.device = Contrib.ThermostatDevice(tuya_id, local_ip, tuya_local_key, version=3.3)

        self.is_synchronized = False

        self._callback_mutex = threading.RLock()
        self._on_callback: TuyaCallbackOnAction | None = None

    def connect(self):
        # connect to device and get status
        logging.getLogger(__name__).info(f'Connecting to device [{self.tuya_id}] IP [{self.local_ip}] Local Key [{self.tuya_local_key}]')

        data = self._get_data(all_data=True)
        logging.getLogger(__name__).debug(f'Device status: [{data}]\n')

        if data is not None and 'Error' not in data:
            had_state_updates = self._process_data_updates(data)
            if had_state_updates:
                self.is_synchronized = True
            logging.getLogger(__name__).info(f'Connected to device [{self.tuya_id}] IP [{self.local_ip}] | [is_synchronized={self.is_synchronized}]')

        elif data is not None and 'Error' in data:
            self.is_synchronized = False
            logging.getLogger(__name__).error(f'Failed to connect to device [{self.tuya_id}] IP [{self.local_ip}] | [{data}]')

        else:
            logging.getLogger(__name__).warning(f'Maybe connected to device [{self.tuya_id}] IP [{self.local_ip}] | [is_synchronized={self.is_synchronized}]')

    def start_monitoring(self, max_iterations: int = 0):
        logging.getLogger(__name__).info(f"Start monitoring [{self.name}] for [x{max_iterations}]")

        # the thermostat will close the connection if it doesn't get a heartbeat message every ~28 seconds, so make sure to ping it.
        # every 9 seconds, or roughly 3x that limit, is a good number to make sure we don't miss it due to received messages resetting the socket timeout
        self.ping_time = time.time() + 9

        iteration = 1

        if max_iterations > 0:
            loop_condition = lambda i: i <= max_iterations
        else:
            loop_condition = lambda i: True

        while loop_condition(iteration):
            logging.getLogger(__name__).info(f'# [{iteration}/{max_iterations}]')

            if self.ping_time <= time.time():
                self.device.sendPing()
                self.ping_time = time.time() + 9

            data = self._get_data()
            if data:
                self.print_data(data)

                had_state_updates = self._process_data_updates(data)

                if had_state_updates and not self.is_synchronized:
                    self.is_synchronized = True

            iteration = self._increment_iteration(iteration, data)

    @staticmethod
    def _increment_iteration(iteration: int, data: Dict | None) -> int:
        if data is None or 'Error' not in data:
            iteration += 1
        if iteration > 2000:
            iteration = 1

        return iteration

    def _get_data(self, all_data:bool = False) -> Dict:
        logging.getLogger(__name__).debug(f'Get data(all_data={all_data}) | [is_synchronized={self.is_synchronized}]')

        if self.is_synchronized and not all_data:
            data = self.device.receive()
        else:
            data = self.device.status()

        if data is not None and 'Error' in data:
            self.is_synchronized = False

        logging.getLogger(__name__).debug(f'>>>> data: [{data}]')
        return data

    def _process_data_updates(self, data: Dict) -> bool:
        logging.getLogger(__name__).debug(f'Processing updates from [{self.name}] with data=[{data}] | [is_synchronized={self.is_synchronized}]')

        had_state_updates = False

        if 'dps' in data and len(data['dps']) > 0:
            dps_data = data.get('dps', {})
            for k,v in dps_data.items():
                metric_id = int(k)
                update_result = self._process_data_update(metric_id, v)
                had_state_updates = had_state_updates or update_result

        return had_state_updates

    def _process_data_update(self, metric_id: int, metric_value: str) -> bool:
        logging.getLogger(__name__).debug(f'Processing update from [{self.name}] to metric=[{metric_id}] value=[{metric_value}]')

        if metric_value is None:
            logging.getLogger(__name__).warning(f'Failed to process update from [{self.name}] to metric=[{metric_id}] value=[{metric_value}]. Null value.')
            return False

        if metric_id == MOES_POWER_STATUS:
            logging.getLogger(__name__).debug(f'POWER_STATUS = [{metric_value}]')
            self.is_on = bool(metric_value)
            logging.getLogger(__name__).info(f'is_on is [{self.is_on}]')

        elif metric_id == MOES_TARGET_TEMPERATURE:
            logging.getLogger(__name__).debug(f'TARGET_TEMPERATURE = [{metric_value}]')
            self.target_temperature = round(int(metric_value) / MOES_TEMPERATURE_SCALE, 1)
            logging.getLogger(__name__).info(f'target_temperature is [{self.target_temperature}]')

        elif metric_id == MOES_MEASURED_TEMPERATURE:
            logging.getLogger(__name__).debug(f'MEASURED_TEMPERATURE = [{metric_value}]')
            self.home_temperature = round(int(metric_value) / MOES_TEMPERATURE_SCALE, 1)
            logging.getLogger(__name__).info(f'home_temperature is [{self.home_temperature}]')

        elif metric_id == MOES_OPERATING_MODE:
            logging.getLogger(__name__).debug(f'OPERATING_MODE = [{metric_value}]')
            self.manual_operating_mode = (metric_value == '1')
            logging.getLogger(__name__).info(f'manual_operating_mode is [{self.manual_operating_mode}]')

        elif metric_id == MOES_ECO_MODE_ENABLED:
            logging.getLogger(__name__).debug(f'ECO_MODE_ENABLED = [{metric_value}]')
            self.eco_mode = bool(metric_value)
            logging.getLogger(__name__).info(f'eco_mode is [{self.eco_mode}]')

        elif metric_id == MOES_LOCK_ENABLED:
            logging.getLogger(__name__).debug(f'LOCK_ENABLED = [{metric_value}]')
            self.lock_enabled = bool(metric_value)
            logging.getLogger(__name__).info(f'lock_enabled is [{self.lock_enabled}]')

        elif metric_id == 102 or metric_id == 104:
            logging.getLogger(__name__).debug(f'IGNORE UNUSED: [{metric_id}]=[{metric_value}]')

        else:
            logging.getLogger(__name__).warning(f'Unknown metric from [{self.name}]: metric=[{metric_id}] value=[{metric_value}].')

        return True

    @property
    def on_callback(self) -> TuyaCallbackOnAction | None:
        """The callback called when the tuya device gets updates.
        """
        return self._on_callback

    @on_callback.setter
    def on_callback(self, func: TuyaCallbackOnAction | None) -> None:
        with self._callback_mutex:
            self._on_callback = func

    def turn_on(self):
        logging.getLogger(__name__).info(f"Turn [{self.name}] ON")
        self.device.turn_on()

        self.is_on = True
        logging.getLogger(__name__).info(f"Set [{self.name}] [is_on] to [{self.is_on}]")

    def turn_off(self):
        logging.getLogger(__name__).info(f"Turning [{self.name}] OFF")
        self.device.turn_off()

        self.is_on = False
        logging.getLogger(__name__).info(f"Set [{self.name}] [is_on] to [{self.is_on}]")

    def set_target_temperature(self, temperature: float):
        logging.getLogger(__name__).debug(f'setTemperature({temperature})')

        if temperature < 5.0:
            temperature = 5.0
        if temperature > 35.0:
            temperature = 35.0

        logging.getLogger(__name__).info(f"Setting [{self.name}] temperature to [{str(temperature) + '°C'}]")
        moes_temp = int(temperature * MOES_TEMPERATURE_SCALE)

        logging.getLogger(__name__).debug(f"setMoesTemperature({moes_temp})")
        self.device.set_value(MOES_TARGET_TEMPERATURE, moes_temp)

        self.target_temperature = temperature
        logging.getLogger(__name__).info(f"Set [{self.name}] [temperature] to [{self.target_temperature}]")

    def set_manual_operating_mode(self, enabled: bool):
        logging.getLogger(__name__).info(f"Setting [{self.name}] operating mode [{'MANUAL' if enabled else 'AUTO'}]")

        moes_op_mode_value = '1' if enabled else '0'
        self.device.set_value(index=MOES_OPERATING_MODE, value=moes_op_mode_value, nowait=True)

        self.manual_operating_mode = enabled
        logging.getLogger(__name__).info(f"Set [{self.name}] [manual_operating_mode] to [{self.manual_operating_mode}]")

    def set_eco_mode(self, eco_mode: bool):
        logging.getLogger(__name__).info(f"Setting [{self.name}] eco mode [{'ON' if eco_mode else 'OFF'}]")
        self.device.set_value(MOES_ECO_MODE_ENABLED, eco_mode)

        self.eco_mode = eco_mode
        logging.getLogger(__name__).info(f"Set [{self.name}] [eco_mode] to [{self.eco_mode}]")

    def set_lock(self, lock_enabled: bool):
        logging.getLogger(__name__).info(f"Setting [{self.name}] lock mode [{'ON' if lock_enabled else 'OFF'}]")
        self.device.set_value(MOES_LOCK_ENABLED, lock_enabled)

        self.lock_enabled = lock_enabled
        logging.getLogger(__name__).info(f"Set [{self.name}] [lock_enabled] to [{self.lock_enabled}]")



    @staticmethod
    def print_data(data):
        if 'dps' in data and len(data['dps']) > 0:
            logging.getLogger(__name__).info(f'>>>> RAW DPS: [{data["dps"]}]')
