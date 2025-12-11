#!/usr/bin/env python
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass, asdict

import json

from generic.dataclass_util import get_valid_dataclass_fields

##########################################################################################################


MqttCallbackOnMessage = Callable[["Client", Any, Dict[str, Any]], None]
TuyaCallbackOnAction = Callable[["Client", Any, Dict[str, Any]], None]


##########################################################################################################
@dataclass
class BridgeData(object):
    is_on: Optional[bool] = None
    target_temperature: Optional[float] = None
    home_temperature: Optional[float] = None
    manual_operating_mode: Optional[int] = None
    eco_mode: Optional[bool] = None
    lock_enabled: Optional[bool] = None

    def __str__(self):
        return (f'BridgeData({self.is_on},'
                f'{self.target_temperature},{self.home_temperature},{self.manual_operating_mode},'
                f'{self.eco_mode},{self.lock_enabled})')

    def to_json(self):
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(dictionary) -> "BridgeData":
        sanitised_parameters = get_valid_dataclass_fields(BridgeData, dictionary)
        return BridgeData(**sanitised_parameters)
##########################################################################################################