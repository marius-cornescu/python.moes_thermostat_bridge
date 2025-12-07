#!/usr/bin/env python
from typing import Any, Callable, Dict, Iterator, List, NamedTuple, Sequence, Tuple, Union, cast

##########################################################################################################




MqttCallbackOnMessage = Callable[["Client", Any, Dict[str, Any]], None]
TuyaCallbackOnAction = Callable[["Client", Any, Dict[str, Any]], None]

