from __future__ import unicode_literals, print_function, division
from veil.model.event import *
import atexit
import signal
import os

EVENT_PROCESS_SETUP = define_event('process-setup')
EVENT_PROCESS_TEARDOWN = define_event('process-teardown')

def handle_exit_signals(signum, frame):
    publish_event(EVENT_PROCESS_TEARDOWN)
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum) # Rethrow signal

atexit.register(publish_event, EVENT_PROCESS_TEARDOWN)
signal.signal(signal.SIGTERM, handle_exit_signals)
signal.signal(signal.SIGINT, handle_exit_signals)