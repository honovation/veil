from __future__ import unicode_literals, print_function, division
import logging
import functools
import time
import threading
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from veil_component import VEIL_ENV, VEIL_HOME, VEIL_FRAMEWORK_HOME
from veil.frontend.website_setting import list_website_components

LOGGER = logging.getLogger(__name__)


def source_code_monitored(func):
    @functools.wraps(func)
    def wrapper(*args):
        purpose = args[0]
        components = list_website_components(purpose)
        LOGGER.info('load components: %(components)s', {'components': components})
        if VEIL_ENV.is_dev:
            if load_components(components):
                SourceCodeMonitor().start()
                return func(*args)
            else:
                time.sleep(3)
                os._exit(1)
        else:
            assert load_components(components)
            return func(*args)

    return wrapper


class SourceCodeMonitor(threading.Thread):
    def __init__(self):
        super(SourceCodeMonitor, self).__init__()
        self.daemon = True

    def run(self):
        application_dir_observer = Observer()
        application_dir_observer.schedule(ReloadEventHandler(), VEIL_HOME, recursive=True)
        application_dir_observer.start()

        framework_dir_observer = Observer()
        framework_dir_observer.schedule(ReloadEventHandler(), VEIL_FRAMEWORK_HOME, recursive=True)
        framework_dir_observer.start()


class ReloadEventHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if not event.is_directory and ('.py' in event.src_path or 'DEP-DYNAMIC-MANUAL' in event.src_path):
            LOGGER.info('event type: %(type)s, path: %(path)s', {'type': event.event_type, 'path': event.src_path})
            os._exit(1)


def load_components(components):
    before = time.time()
    for component in components:
        try:
            __import__(component)
        except Exception:
            LOGGER.exception('failed to load component: %(component)s', {'component': component})
            return False
    after = time.time()
    LOGGER.info('all components loaded: took %(elapsed_seconds)s seconds', {'elapsed_seconds': after - before})
    return True
