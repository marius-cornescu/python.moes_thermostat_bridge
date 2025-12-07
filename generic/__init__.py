#!/usr/bin/env python
import sys
import signal
import atexit

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

