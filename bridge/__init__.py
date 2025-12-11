#!/usr/bin/env python
from typing import Any, Callable, Dict, Iterator, List, NamedTuple, Sequence, Tuple, Union, get_origin, Optional, Type, get_type_hints
import logging
from dataclasses import dataclass, field, asdict, fields

import json

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
        sanitised_parameters = sanitized_dataclass_fields(BridgeData, dictionary)
        return BridgeData(**sanitised_parameters)
##########################################################################################################

def sanitized_dataclass_fields(dataclass_type: Type, data: Dict[str, Any]) -> Dict[str, Any]:
    # Get the type hints of the dataclass fields
    type_hints = get_type_hints(dataclass_type)

    # Remove keys that are not fields
    sanitised_data = {k: v for k, v in data.items() if k in type_hints}

    invalid_type_fields = get_invalid_type_dataclass_fields(dataclass_type=dataclass_type, data=sanitised_data)
    # Remove keys with values are not same type as fields
    sanitised_data = {k: v for k, v in sanitised_data.items() if k not in invalid_type_fields}

    return sanitised_data

def get_invalid_type_dataclass_fields(dataclass_type: Type, data: Dict[str, Any]) -> List[str]:
    # Get the type hints of the dataclass fields
    type_hints = get_type_hints(dataclass_type)

    invalid_type_fields = []

    # Validate types
    for f, value in data.items():
        expected_type = type_hints[f]
        is_valid, expected_type =validate_value_matches_field_type(expected_type, value)

        if not is_valid:
            logging.getLogger(__name__).warning(f"Field [{f}] must be of type [{expected_type}], got [{type(value).__name__}]")
            invalid_type_fields.append(f)

    return invalid_type_fields

def validate_value_matches_field_type(expected_type, value) -> Tuple[bool, Any]:
    is_valid = True
    origin = get_origin(expected_type)

    if origin is Union:
        # Handle Optional (Union[T, None])
        args = expected_type.__args__
        if len(args) == 2 and type(None) in args:
            # This is Optional[T], so value can be None or of type T
            non_none_type = next(arg for arg in args if arg is not type(None))
            if value is not None and not isinstance(value, non_none_type):
                expected_type = non_none_type.__name__
                is_valid = False
        else:
            # Regular Union (not Optional)
            if not isinstance(value, expected_type):
                is_valid = False
    else:
        # Not a Union (not Optional)
        if not isinstance(value, expected_type):
            expected_type = expected_type.__name__
            is_valid = False

    return is_valid, expected_type

##########################################################################################################