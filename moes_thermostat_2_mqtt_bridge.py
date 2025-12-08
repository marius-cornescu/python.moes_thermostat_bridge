#!/usr/bin/env python
import sys
import os

import argparse
import datetime

import app
from generic import setup_cleanup_on_exit, callback_on_exit


##########################################################################################################


def main():
    class Args:
        """Custom class to hold application arguments."""

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    def get_env_variable(name, default=None, var_type=str):
        """Helper function to get environment variables with type conversion."""
        value = os.getenv(name, default)
        if value is not None and var_type != str:
            try:
                return var_type(value)
            except ValueError:
                raise ValueError(f"Environment variable [{name}] must be of type [{var_type.__name__}]")
        return value

    # Read environment variables
    target_env = get_env_variable('MC_APP_TARGET_ENV', var_type=str)
    tuya_dev_id = get_env_variable('MC_APP_TUYA_DEV_ID', var_type=str)
    tuya_dev_ip = get_env_variable('MC_APP_TUYA_DEV_IP', var_type=str)
    tuya_dev_local_key = get_env_variable('MC_APP_TUYA_DEV_LOCAL_KEY', var_type=str)
    mqtt_broker_addr = get_env_variable('MC_APP_MQTT_BROKER_ADDR', var_type=str)
    mqtt_broker_port = get_env_variable('MC_APP_MQTT_BROKER_PORT', default=8883, var_type=int)
    mqtt_user = get_env_variable('MC_APP_MQTT_USER', var_type=str)
    mqtt_password = get_env_variable('MC_APP_MQTT_PASSWORD', var_type=str)
    mqtt_tls_path = get_env_variable('MC_APP_MQTT_TLS_PATH', var_type=str)
    static_data = get_env_variable('MC_APP_STATIC_DATA', default=False, var_type=bool)

    # Pass the arguments to the app
    args = argparse.Namespace(
        target_env=target_env,
        tuya_dev_id=tuya_dev_id,
        tuya_dev_ip=tuya_dev_ip,
        tuya_dev_local_key=tuya_dev_local_key,
        mqtt_broker_addr=mqtt_broker_addr,
        mqtt_broker_port=mqtt_broker_port,
        mqtt_user=mqtt_user,
        mqtt_password=mqtt_password,
        mqtt_tls_path=mqtt_tls_path,
        static_data=static_data,
    )

    app.run_app(args)


##########################################################################################################

if __name__ == '__main__':
    start_time = datetime.datetime.now()
    sys.__stdout__.write('%s \n' % start_time.ctime())
    sys.__stdout__.flush()

    try:
        setup_cleanup_on_exit()
        main()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("KeyboardInterrupt received, exiting...")
        callback_on_exit()

    end_time = datetime.datetime.now()
    sys.__stdout__.write('%s \n' % end_time.ctime())
    sys.__stdout__.write('TOTAL DURATION = %s \n' % (end_time - start_time))
    sys.__stdout__.flush()
