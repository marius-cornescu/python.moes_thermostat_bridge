#!/usr/bin/env python
from typing import Any, List, Optional, Dict
import logging
import sys
from io import IOBase

from .config import ActiveConfig


##########################################################################################################


class DefaultStreamHandler(logging.StreamHandler):
    def __init__(self, stream=sys.__stdout__):
        # Use the original sys.__stdout__ to write to stdout
        # for this handler, as sys.stdout will write out to logger.
        super().__init__(stream)


class LoggerWriter(IOBase):
    """Class to replace the stderr/stdout calls to a logger"""

    def __init__(self, logger_name: str, log_level: int, app_name: str):
        """:param logger_name: Name to give the logger (e.g. 'stderr')
        :param log_level: The log level, e.g. logging.DEBUG / logging.INFO that
                          the MESSAGES should be logged at.
        """
        self.std_logger = logging.getLogger(logger_name)
        # Get the "root" logger from by its name (i.e. from a config dict or at the bottom of this file)
        #  We will use this to create a copy of all its settings, except the name
        app_logger = logging.getLogger(app_name)
        [self.std_logger.addHandler(handler) for handler in app_logger.handlers]
        self.std_logger.setLevel(app_logger.level)  # the minimum lvl msgs will show at
        self.level = log_level  # the level msgs will be logged at
        self.buffer = []
        self.encoding = 'utf-8'

    def write(self, msg: str):
        """Stdout/stderr logs one line at a time, rather than 1 message at a time.
        Use this function to aggregate multi-line messages into 1 log call."""
        msg = msg.decode() if issubclass(type(msg), bytes) else msg

        if not msg.endswith("\n"):
            return self.buffer.append(msg)

        self.buffer.append(msg.rstrip("\n"))
        message = "".join(self.buffer)
        self.std_logger.log(self.level, message)
        self.buffer = []


##########################################################################################################

def __replace_stderr_and_stdout_with_logger(ac: ActiveConfig):
    """Replaces calls to sys.stderr -> logger.info & sys.stdout -> logger.error"""
    # To access the original stdout/stderr, use sys.__stdout__/sys.__stderr__

    if ac.stdout is None:
        ac.stdout = LoggerWriter("stdout", logging.INFO, ac.app_name)
        sys.stdout = ac.stdout

    if ac.stderr is None:
        ac.stderr = LoggerWriter("stderr", logging.ERROR, ac.app_name)
        sys.stderr = ac.stderr


##########################################################################################################

def __create_console_handler(ac: ActiveConfig):
    # create console handler and set level to debug
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(' %(process)d | %(asctime)s | %(levelname)s | %(name)s | %(message)s'))

    return handler


def __create_file_handler(ac: ActiveConfig):
    from datetime import datetime

    log_filename = ac.config.log_file_pattern.format(
        timestamp=datetime.now().strftime('%Y%m%d_%H%M%S'),
        app_name=ac.app_name,
    )

    handler = logging.FileHandler(log_filename)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(' %(process)d | %(asctime)s | %(levelname)s | %(name)s | %(message)s'))

    return handler


def init_logging(ac: ActiveConfig):
    root_logger = logging.getLogger()
    ac.logging = logging.getLogger(ac.app_name)

    # add console_handler to root logger
    root_logger.addHandler(__create_console_handler(ac))
    if ac.config.log_file_pattern is not None:
        root_logger.addHandler(__create_file_handler(ac))

    root_logger.setLevel(ac.config.log_level_root)

    ac.logging.setLevel(ac.config.log_level_app)

    set_log_level_for_all(['generic.progress'], ac.config.log_level_app)
    set_log_level_for_all(['bridge', 'bridge.bridge'], ac.config.log_level_app_bridge)
    set_log_level_for_all(['tinytuya', 'tinytuya.core', 'tinytuya.core.XenonDevice', 'tinytuya.core.crypto_helper',
                           'tinytuya.core.message_helper', 'tinytuya.core.error_helper'], ac.config.log_level_tuya)

    ac.cli_out = LoggerWriter('cli_out', logging.DEBUG, ac.app_name)

    __replace_stderr_and_stdout_with_logger(ac)

    return ac.logging

def set_log_level_for_all(app_logger_names: List[str], log_level: int):
    for logger_name in app_logger_names:
        logging.getLogger(logger_name).setLevel(log_level)

##########################################################################################################