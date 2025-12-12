#!/usr/bin/env python
from typing import Any, Final, Optional
import logging

import threading

from .progress import Progress

##########################################################################################################

COMMON_APPS = [
    'git-test-repo',
]

##########################################################################################################
class Config:
    debug: bool

    log_file_pattern: str

    log_level_root: int
    log_level_app: int
    log_level_tuya: int

##########################################################################################################
class DEVConfig(Config):
    debug = True

    log_file_pattern = None

    log_level_root = logging.DEBUG
    log_level_app = logging.DEBUG
    log_level_tuya = logging.INFO

##########################################################################################################
class PRODConfig(Config):
    debug = False

    log_file_pattern = 'logs/{timestamp}_{app_name}.log'

    log_level_root = logging.WARNING
    log_level_app = logging.INFO
    log_level_tuya = logging.WARNING

##########################################################################################################
DEV: Final = DEVConfig()
PROD: Final = PRODConfig()
##########################################################################################################
CONFIGURATIONS = {
    "DEV": DEV,
    "PROD": PROD,
}
##########################################################################################################


class ActiveConfig(object):

    def __init__(self, app_name: str, config: Config):
        self.app_name = app_name
        self.config = config
        self.logging = None
        self.stdout = None
        self.stderr = None
        self.azure_cli_out = None
        self.progress = Progress()

    @staticmethod
    def get_active_config(target_env, app_name: str) -> 'ActiveConfig':
        active_config = ActiveConfig(app_name, config=CONFIGURATIONS.get(target_env, DEVConfig))

        return active_config
    
##########################################################################################################
# Singleton helpers for ActiveConfig
##########################################################################################################

_logger = logging.getLogger(__name__)
_active_config: Optional[ActiveConfig] = None
_active_config_lock = threading.Lock()

def set_active_config(target_env: str, app_name: str) -> ActiveConfig:
    """Initialize the single ActiveConfig instance (first caller wins). Subsequent calls are ignored."""
    global _active_config
    with _active_config_lock:
        if _active_config is None:
            cfg = CONFIGURATIONS.get(target_env, DEV)
            _active_config = ActiveConfig(app_name=app_name, config=cfg)
            _logger.info("ActiveConfig initialized: env=%s app_name=%s", target_env, app_name)
        else:
            # If caller passes different values, log and ignore to preserve the first initialization
            if _active_config.app_name != app_name or _active_config.config is not CONFIGURATIONS.get(target_env):
                _logger.warning(
                    "set_active_config called after initialization; ignoring new parameters (existing app_name=%s env=%s)",
                    _active_config.app_name,
                    # try to find env key for existing config (best-effort)
                    next((k for k, v in CONFIGURATIONS.items() if v is _active_config.config), "unknown"),
                )
    return _active_config

def get_active_config() -> ActiveConfig:
    """Return the initialized ActiveConfig. If not initialized, initialize it with defaults (DEV, APP_NAME)."""
    global _active_config
    if _active_config is None:
        return set_active_config("DEV", __name__)
    return _active_config

def get_app_name() -> str:
    """Convenience accessor for the application name."""
    return get_active_config().app_name

##########################################################################################################