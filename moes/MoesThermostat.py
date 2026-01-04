#!/usr/bin/env python
from typing import Any, Final, Optional, Dict
import logging
from dataclasses import dataclass, asdict

import json
import time
import threading
import traceback
import copy

from tinytuya import Contrib

from generic import try_get_from_structure, dict_map_keys, dict_filter_none
from generic.dataclass_util import get_valid_dataclass_fields
from bridge import TuyaCallbackOnAction

##########################################################################################################

# 'dps': {'1': True, '2': 40, '3': 40, '4': '0', '5': False, '6': False, '102': 0, '104': True}
#        {'1': True, '2': 46, '3': 41, '4': '0', '5': False, '6': False, '102': 0, '104': True}
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

ITERATION_INDEX_LIMIT = 2000

MOES_TEMPERATURE_SCALE = 2

##########################################################################################################
@dataclass
class ThermostatState(object):
    is_on: Optional[bool] = None
    target_temperature: Optional[float] = None
    home_temperature: Optional[float] = None
    manual_operating_mode: Optional[bool] = None
    eco_mode: Optional[bool] = None
    lock_enabled: Optional[bool] = None

    def clone(self):
        return copy.deepcopy(self)

    def to_json(self):
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(dictionary) -> "ThermostatState":
        sanitised_parameters = get_valid_dataclass_fields(ThermostatState, dictionary)
        return ThermostatState(**sanitised_parameters)

##########################################################################################################

class MoesBht002Thermostat(Contrib.ThermostatDevice):
    __POWER_STATUS = 1
    __TARGET_TEMPERATURE = 2
    __MEASURED_TEMPERATURE = 3
    __OPERATING_MODE = 4
    __ECO_MODE = 5
    __LOCK_ENABLED = 6

    __IGNORE_METRIC1 = 102
    __IGNORE_METRIC2 = 104

    moes_metric_map = {
        __POWER_STATUS:         'is_on',
        __TARGET_TEMPERATURE:   'target_temperature',
        __MEASURED_TEMPERATURE: 'home_temperature',
        __OPERATING_MODE:       'manual_operating_mode',
        __ECO_MODE:             'eco_mode',
        __LOCK_ENABLED:         'lock_enabled',
        __IGNORE_METRIC1:       None,
        __IGNORE_METRIC2:       None,
    }

    dps_data = {
        f'{__TARGET_TEMPERATURE}':  {'name': 'target_temperature', 'alt': 'setpoint_c', 'scale': 2},
        f'{__MEASURED_TEMPERATURE}':{'name': 'home_temperature', 'alt': 'temperature_c', 'scale': 2},
        f'{__OPERATING_MODE}':      {'name': 'manual_operating_mode', 'enum': ['0','1']},
        f'{__ECO_MODE}':            {'name': 'eco_mode', 'decode': bool},
        f'{__LOCK_ENABLED}':        {'name': 'lock_enabled', 'decode': bool},
        f'{__IGNORE_METRIC1}':      {'name': 'ignore_1', 'decode': int},
        f'{__IGNORE_METRIC2}':      {'name': 'ignore_2', 'decode': bool}
    }

    def __init__(self, *args, **kwargs):
        super(MoesBht002Thermostat, self).__init__(*args, **kwargs)

    def map_dps_metric_to_state(self, dps_metric_id: str) -> str | None:
        try:
            return self.moes_metric_map.get(int(dps_metric_id), None)
        except Exception as e:
            logging.getLogger(__name__).error(f'Exception while _map_dps_metric_to_state [{dps_metric_id}]: [%s]', e)
            if logging.getLogger(__name__).isEnabledFor(logging.ERROR):
                traceback.print_exc()

        return None

    def map_state_to_dps_metric(self, state_field: str) -> int | None:
        for key, value in self.moes_metric_map.items():
            if value == state_field:
                return key
        return None

##########################################################################################################

@dataclass
class MoesBhtThermostat(object):
    name: str
    tuya_id: str
    local_ip: str
    tuya_local_key: str

    device: Final[MoesBht002Thermostat]

    state_current: ThermostatState
    state_previous: ThermostatState

    # delay between when a new full status should be retrieved, even if in sync
    full_status_get_delay_seconds: int = 1 * 60
    # delay between when a new full status should be published
    full_status_publish_delay_seconds: int = 10 * 60

    is_synchronized: Optional[bool] = False

    ping_time: Optional[float] = None

    # when should next full status be sent
    full_status_get_time: Optional[float] = None
    full_status_publish_time: Optional[float] = None

    is_connection_lost: bool = False

    def __init__(self, name: str, tuya_id: str, local_ip: str, tuya_local_key: str,
                 device: MoesBht002Thermostat | None = None):
        self.name = name
        self.tuya_id = tuya_id
        self.local_ip = local_ip
        self.tuya_local_key = tuya_local_key

        if device is None:
            device = MoesBht002Thermostat(tuya_id, local_ip, tuya_local_key, version=3.3)
        self.device = device

        self.state_current = ThermostatState(
            is_on=False,
            target_temperature=0.0,
            home_temperature=0.0,
            manual_operating_mode=False,
            eco_mode=False,
            lock_enabled=False
        )
        self.state_previous = self.state_current

        self.is_synchronized = False

        self._in_synchronize_mutex = threading.Lock()

        self._callback_mutex = threading.RLock()
        self._in_callback_mutex = threading.Lock()
        self._on_callback: TuyaCallbackOnAction | None = None

    def connect(self):
        logging.getLogger(__name__).debug(f'Connecting to [{self.tuya_id}] IP [{self.local_ip}] Local Key [{self.tuya_local_key}]')

        data = self._get_data(all_data=True)
        logging.getLogger(__name__).debug(f'Device status: [{data}]\n')

        if data is not None and 'Error' not in data:
            had_state_updates = self._process_raw_data_updates(data)
            if had_state_updates:
                self.is_synchronized = True
            logging.getLogger(__name__).info(f'Connected to [{self.tuya_id}] IP [{self.local_ip}] | [is_synchronized={self.is_synchronized}]')

        elif data is not None and 'Error' in data:
            self.is_synchronized = False
            logging.getLogger(__name__).error(f'Failed to connect to device [{self.tuya_id}] IP [{self.local_ip}] | [{data}]')

        else:
            logging.getLogger(__name__).warning(f'Maybe connected to device [{self.tuya_id}] IP [{self.local_ip}] | [is_synchronized={self.is_synchronized}]')

    def start_monitoring(self, max_iterations: int = 0):
        logging.getLogger(__name__).info(f'Start monitoring [{self.name}] for [x{max_iterations}]')

        self.ping_time = self._next_ping_time()
        self.full_status_get_time = time.time() + self.full_status_get_delay_seconds
        self.full_status_publish_time = time.time() + self.full_status_publish_delay_seconds

        iteration = 1

        if max_iterations > 0:
            loop_condition = lambda i: i <= max_iterations
        else:
            loop_condition = lambda i: True

        while loop_condition(iteration):
            logging.getLogger(__name__).info(f'# [ {iteration:4d} / {max_iterations:4d} ]')

            if self.ping_time > time.time():
                self.device.sendPing()
                self.ping_time = self._next_ping_time()

            data = self._get_data()
            if data:
                if 'Error' not in data:
                    had_state_updates = self._process_raw_data_updates(data)
                    self.__set_connection_restored()

                    if had_state_updates and not self.is_synchronized:
                        self.is_synchronized = True

                else:
                    self.__set_connection_lost()

            iteration = self._increment_iteration(iteration, data)

    @staticmethod
    def _increment_iteration(iteration: int, data: Dict | None) -> int:
        if data is None or 'Error' not in data:
            iteration += 1
        if iteration > ITERATION_INDEX_LIMIT:
            iteration = 1

        return iteration

    @staticmethod
    def _next_ping_time() -> float:
        """ the thermostat will close the connection if it doesn't get a heartbeat message every ~28 seconds, so make sure to ping it.
        every 9 seconds, or roughly 3x that limit, is a good number to make sure we don't miss it due to received messages resetting the socket timeout
        """
        return time.time() + 9

    def _get_data(self, all_data: bool = False) -> Dict:
        logging.getLogger(__name__).debug(f'Get data(all_data={all_data}) | [is_synchronized={self.is_synchronized}]')

        if self.is_synchronized and not all_data and self.full_status_get_time > time.time():
            data = self.device.receive()
        else:
            data = self.device.status()
            self.full_status_get_time = time.time() + self.full_status_get_delay_seconds

        if data is not None and 'Error' in data:
            self.is_synchronized = False

        logging.getLogger(__name__).debug(f'>>>> data: [{data}]')
        return data

    def _process_raw_data_updates(self, data: Dict) -> bool:
        logging.getLogger(__name__).debug(f'Processing updates for [{self.name}] with data=[{data}] | [is_synchronized={self.is_synchronized}]')

        had_state_updates = False

        dps_data = try_get_from_structure(data, ['dps'])

        if dps_data is not None:
            state_data = dict_map_keys(dps_data, self.device.map_dps_metric_to_state)
            had_state_updates = self._process_data_updates(state_data)
        else:
            logging.getLogger(__name__).debug('No DPS data available')

        logging.getLogger(__name__).debug(f'Processed updates for [{self.name}] => had_state_updates=[{had_state_updates}]')
        return had_state_updates

    def _process_data_updates(self, state_data: Dict[str, Any]) -> bool:
        logging.getLogger(__name__).debug(f'Processing updates for [{self.name}] with data=[{state_data}] | [is_synchronized={self.is_synchronized}]')
        had_state_updates = False

        state_data = dict_filter_none(state_data)

        if len(state_data) > 0:

            with self._in_synchronize_mutex:
                current_state_backup = self.state_current.clone()

                for state_field, v in state_data.items():
                    update_result = self.__process_data_update(state_field, v)
                    had_state_updates = had_state_updates or update_result

                if had_state_updates and not self.state_current.__eq__(current_state_backup):
                    logging.getLogger(__name__).info(f'State for [{self.name}] updated from [{self.state_previous}] to [{self.state_current}]')
                    self.state_previous = current_state_backup
                    self._handle_on_state_changed()

                elif self.full_status_publish_delay_seconds > time.time():
                    logging.getLogger(__name__).info(f'State REFRESH for [{self.name}] with state [{self.state_current}]')
                    self.full_status_publish_time = time.time() + self.full_status_publish_delay_seconds
                    self._handle_on_state_changed()

        return had_state_updates

    def __process_data_update(self, state_field: str, metric_value: str) -> bool:
        logging.getLogger(__name__).debug(f'Processing update for [{self.name}] to metric=[{state_field}] value=[{metric_value}]')

        if metric_value is None:
            logging.getLogger(__name__).warning(f'Failed to process update for [{self.name}] to metric=[{state_field}] value=[{metric_value}]. Null value.')
            return False

        if state_field == 'is_on':
            logging.getLogger(__name__).debug(f'POWER_STATUS = [{metric_value}]')
            self.state_current.is_on = bool(metric_value)
            logging.getLogger(__name__).info(f'NEW-STATE: is_on is [{self.state_current.is_on}]')

        elif state_field == 'target_temperature':
            logging.getLogger(__name__).debug(f'TARGET_TEMPERATURE = [{metric_value}]')
            self.state_current.target_temperature = round(int(metric_value) / MOES_TEMPERATURE_SCALE, 1)
            logging.getLogger(__name__).info(f'NEW-STATE: target_temperature is [{self.state_current.target_temperature}]')

        elif state_field == 'home_temperature':
            logging.getLogger(__name__).debug(f'MEASURED_TEMPERATURE = [{metric_value}]')
            self.state_current.home_temperature = round(int(metric_value) / MOES_TEMPERATURE_SCALE, 1)
            logging.getLogger(__name__).info(f'NEW-STATE: home_temperature is [{self.state_current.home_temperature}]')

        elif state_field == 'manual_operating_mode':
            logging.getLogger(__name__).debug(f'OPERATING_MODE = [{metric_value}]')
            self.state_current.manual_operating_mode = (metric_value == '1')
            logging.getLogger(__name__).info(f'NEW-STATE: manual_operating_mode is [{self.state_current.manual_operating_mode}]')

        elif state_field == 'eco_mode':
            logging.getLogger(__name__).debug(f'ECO_MODE_ENABLED = [{metric_value}]')
            self.state_current.eco_mode = bool(metric_value)
            logging.getLogger(__name__).info(f'NEW-STATE: eco_mode is [{self.state_current.eco_mode}]')

        elif state_field == 'lock_enabled':
            logging.getLogger(__name__).debug(f'LOCK_ENABLED = [{metric_value}]')
            self.state_current.lock_enabled = bool(metric_value)
            logging.getLogger(__name__).info(f'NEW-STATE: lock_enabled is [{self.state_current.lock_enabled}]')

        else:
            logging.getLogger(__name__).warning(f'NEW-STATE: Unknown metric for [{self.name}]: metric=[{state_field}] value=[{metric_value}].')
            return False

        return True

    def _apply_state_change(self) -> None:
        if self.state_previous.is_on != self.state_current.is_on:
            self.set_is_on(self.state_current.is_on)
        if self.state_previous.target_temperature != self.state_current.target_temperature:
            self.set_target_temperature(self.state_current.target_temperature)
        if self.state_previous.manual_operating_mode != self.state_current.manual_operating_mode:
            self.set_manual_operating_mode(self.state_current.manual_operating_mode)
        if self.state_previous.eco_mode != self.state_current.eco_mode:
            self.set_eco_mode(self.state_current.eco_mode)
        if self.state_previous.lock_enabled != self.state_current.lock_enabled:
            self.set_lock_enabled(self.state_current.lock_enabled)

    def _handle_on_state_changed(self) -> None:
        with self._callback_mutex:
            on_callback = self.on_callback

        if on_callback:
            with self._in_callback_mutex:
                try:
                    on_callback(self, self.state_current.__dict__)
                except Exception as e:
                    logging.getLogger(__name__).error(f'Exception [{self.name}] while _handle_on_state_changed: [%s]', e)
                    if logging.getLogger(__name__).isEnabledFor(logging.ERROR):
                        traceback.print_exc()

    @property
    def on_callback(self) -> TuyaCallbackOnAction | None:
        """The callback called when the tuya device gets updates.
        """
        return self._on_callback

    @on_callback.setter
    def on_callback(self, func: TuyaCallbackOnAction | None) -> None:
        with self._callback_mutex:
            self._on_callback = func

    def set_state(self, new_state: ThermostatState) -> ThermostatState:
        logging.getLogger(__name__).info(f"Set [{self.name}] [state] to [{new_state}]")

        if self._process_data_updates(new_state.__dict__):
            self._apply_state_change()

        return self.state_current

    def turn_on(self):
        self.set_is_on(True)

    def turn_off(self):
        self.set_is_on(False)

    def set_is_on(self, is_on: bool):
        logging.getLogger(__name__).info(f"Set [{self.name}] [is_on] to [{is_on}]")

        if is_on:
            self.device.turn_on()
        else:
            self.device.turn_off()

        self.state_previous = self.state_current.clone()
        self.state_current.is_on = is_on
        logging.getLogger(__name__).info(f"Set [{self.name}] [is_on] to [{self.state_current.is_on}]")

    def set_target_temperature(self, temperature: float):
        logging.getLogger(__name__).debug(f'setTemperature({temperature})')

        if temperature < 5.0:
            temperature = 5.0
        if temperature > 35.0:
            temperature = 35.0

        logging.getLogger(__name__).info(f"Setting [{self.name}] temperature to [{str(temperature) + '°C'}]")
        moes_temp = int(temperature * MOES_TEMPERATURE_SCALE)

        logging.getLogger(__name__).debug(f"setMoesTemperature({moes_temp})")
        self.device.set_value(index=self.device.map_state_to_dps_metric('target_temperature'), value=moes_temp)

        self.state_previous = self.state_current.clone()
        self.state_current.target_temperature = temperature
        logging.getLogger(__name__).info(f"Set [{self.name}] [temperature] to [{self.state_current.target_temperature}]")

    def set_manual_operating_mode(self, enabled: bool):
        logging.getLogger(__name__).info(f"Setting [{self.name}] operating mode [{'MANUAL' if enabled else 'AUTO'}]")

        moes_op_mode_value = '1' if enabled else '0'
        self.device.set_value(index=self.device.map_state_to_dps_metric('manual_operating_mode'), value=moes_op_mode_value, nowait=True)

        self.state_previous = self.state_current.clone()
        self.state_current.manual_operating_mode = enabled
        logging.getLogger(__name__).info(f"Set [{self.name}] [manual_operating_mode] to [{self.state_current.manual_operating_mode}]")

    def set_eco_mode(self, eco_mode: bool):
        logging.getLogger(__name__).info(f"Setting [{self.name}] eco mode [{'ON' if eco_mode else 'OFF'}]")
        self.device.set_value(index=self.device.map_state_to_dps_metric('eco_mode'), value=eco_mode)

        self.state_previous = self.state_current.clone()
        self.state_current.eco_mode = eco_mode
        logging.getLogger(__name__).info(f"Set [{self.name}] [eco_mode] to [{self.state_current.eco_mode}]")

    def set_lock_enabled(self, lock_enabled: bool):
        logging.getLogger(__name__).info(f"Setting [{self.name}] lock mode [{'ON' if lock_enabled else 'OFF'}]")
        self.device.set_value(index=self.device.map_state_to_dps_metric('lock_enabled'), value=lock_enabled)

        self.state_previous = self.state_current.clone()
        self.state_current.lock_enabled = lock_enabled
        logging.getLogger(__name__).info(f"Set [{self.name}] [lock_enabled] to [{self.state_current.lock_enabled}]")


    def __set_connection_lost(self):
        if not self.is_connection_lost:
            self.is_connection_lost = True
            logging.getLogger(__name__).warning(f'Connection: Lost')

    def __set_connection_restored(self):
        if self.is_connection_lost:
            self.is_connection_lost = False
            logging.getLogger(__name__).warning(f'Connection: Restored')
