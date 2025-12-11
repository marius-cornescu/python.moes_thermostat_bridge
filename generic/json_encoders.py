#!/usr/bin/env python
import logging
from typing import Dict, Optional, List, Any

from dataclasses import is_dataclass

from datetime import datetime
import json

##########################################################################################################
class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime(format='%Y-%m-%dT%H:%M:%S.%fZ')
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

    @staticmethod
    def decode_data_object(dct: Dict[str, Any], key: str):
        dt_str = ''
        try:
            dt_str = dct.get(key)
            dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S.%fZ') if dt_str else None
            dct[key] = dt
        except ValueError as e:
            logging.getLogger(__name__).error(f'DateEncoder: Failed to parse [{dt_str}]: [%s]', e)
##########################################################################################################
class DataClassJsonEncoder(DateEncoder):
    def default(self, obj):
        if is_dataclass(obj.__class__):
            return obj.__dict__
        # Let the base class default method raise the TypeError
        return DateEncoder.default(self, obj)
##########################################################################################################