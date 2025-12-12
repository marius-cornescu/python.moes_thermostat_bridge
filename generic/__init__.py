#!/usr/bin/env python
from typing import Dict, List, Any, Callable
import sys
import signal
import atexit
from .version import VERSION

##########################################################################################################
__author__ = 'Marius Cornescu'
__email__ = 'marius_cornescu@yahoo.com'
__copyright__ = '2026'
__version__ = VERSION
##########################################################################################################

##########################################################################################################

on_exit_calls = []

def callback_on_exit():
    sys.__stdout__.write(f"Cleaning up [{on_exit_calls}] resources...\n")
    sys.__stdout__.flush()

    for on_exit_call in on_exit_calls:
        try:
            on_exit_call()
        except BaseException as e:
            sys.__stdout__.write(f"Exception on exit call [{e}]\n")
            sys.__stdout__.flush()

def setup_cleanup_on_exit():
    # Register the cleanup function to be called on normal exit
    atexit.register(callback_on_exit)

    # Define a signal handler for termination signals
    def handle_signal(signum, frame):
        print(f"Received signal [{signum}], exiting gracefully...")
        callback_on_exit()  # Call the cleanup function
        exit(0)

    # Register the signal handler for SIGINT (Ctrl+C) and SIGTERM
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

def register_on_exit_action(on_exit_action):
    print("Registering on_exit action.")
    on_exit_calls.append(on_exit_action)


##########################################################################################################

def try_get_from_structure(structure: Dict, value_path: List[str], default_value: Any = None) -> Any:
    if structure is None or len(structure) == 0:
        return default_value

    if len(value_path) == 1:
        key = value_path.pop(0)
        return structure.get(key, default_value)

    else:
        key = value_path.pop(0)
        return try_get_from_structure(structure.get(key, {}), value_path, default_value)

def try_get_first_non_null_from_structure(structure: Dict, value_paths: list[list[str]], default_value: Any = None) -> Any:
    for value_path in value_paths:
        value = try_get_from_structure(structure, value_path=value_path)
        if value is not None:
            return value
    return default_value

##########################################################################################################

def flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
    """
    Flattens a dictionary of dictionaries into a single-level dict with dot-separated keys.
    Example: {'a': {'b': 1}} -> {'a.b': 1}
    """
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items

##########################################################################################################

def dict_map_keys(original_dict, key_mapping_func: Callable):
    mapped_dict = {}
    for key, value in original_dict.items():
        try:
            new_key = key_mapping_func(key)
            if new_key is not None:
                mapped_dict[new_key] = value
        except Exception:
            continue
    return mapped_dict

##########################################################################################################

def dict_filter_none(d: dict[str, Any]) -> dict[str, Any]:
    """Make dict excluding None values."""
    return {k: v for k, v in d.items() if v is not None}

##########################################################################################################