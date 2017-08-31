from __future__ import unicode_literals, print_function, division
from veil.model.event import *
import atexit
import signal
import os

EVENT_PROCESS_SETUP = define_event('process-setup')
EVENT_PROCESS_TEARDOWN = define_event('process-teardown')


def handle_exit_signals(signum, frame):
    publish_event(EVENT_PROCESS_TEARDOWN, loads_event_handlers=False)
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum)  # Rethrow signal


def register_signal_handlers():
    atexit.register(publish_event, EVENT_PROCESS_TEARDOWN, loads_event_handlers=False)
    signal.signal(signal.SIGTERM, handle_exit_signals)
    signal.signal(signal.SIGINT, handle_exit_signals)
    signal.signal(signal.SIGQUIT, handle_exit_signals)


register_signal_handlers()
