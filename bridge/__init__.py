#!/usr/bin/env python
from typing import Any, Callable, Dict, Optional

##########################################################################################################

# Callable [ <in arguments> = [ <self>, <parameter_1>, .... ], <out type> ]
MqttCallbackOnMessage = Callable[["MqttClient", Dict[str, Any]], None]
TuyaCallbackOnAction = Callable[["MoesBhtThermostat", Dict[str, Any]], None]

##########################################################################################################

##########################################################################################################