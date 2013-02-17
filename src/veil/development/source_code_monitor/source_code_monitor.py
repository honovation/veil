from __future__ import unicode_literals, print_function, division
import logging
import functools
import time
import threading
import discipline_coach
import os
from veil.environment import *

LOGGER = logging.getLogger(__name__)


def source_code_monitored(func):
    @functools.wraps(func)
    def wrapper(**kwargs):
        components = kwargs.pop('components')
        LOGGER.info('load components: %(components)s', {'components': components})
        if 'development' == VEIL_ENV:
            if load_components(components):
                SourceCodeMonitor().start()
                return func(**kwargs)
            else:
                time.sleep(3)
                os._exit(1)
        else:
            assert load_components(components)
            return func(**kwargs)

    return wrapper


class SourceCodeMonitor(threading.Thread):
    def __init__(self):
        super(SourceCodeMonitor, self).__init__()
        self.daemon = True
        self.init_app_base_version, self.init_app_changes = discipline_coach.get_git_dir_version(VEIL_HOME)
        self.init_framework_base_version, self.init_framework_changes = discipline_coach.get_git_dir_version(
            VEIL_FRAMEWORK_HOME)

    def run(self):
        while True:
            try:
                time.sleep(0.5)
                if self.detect_change():
                    os._exit(1)
            except:
                LOGGER.exception('source code monitor died')

    def detect_change(self):
        current_app_base_version, current_app_changes = discipline_coach.get_git_dir_version(VEIL_HOME)
        if current_app_base_version != self.init_app_base_version:
            LOGGER.info('application base version changed: reload now')
            return True
        if is_python_source_code_changed(self.init_app_changes, current_app_changes):
            LOGGER.info('application python source code changed: reload now')
            return True
        current_framework_base_version, current_framework_changes = discipline_coach.get_git_dir_version(
            VEIL_FRAMEWORK_HOME)
        if current_framework_base_version != self.init_framework_base_version:
            LOGGER.info('framework base version changed: reload now')
            return True
        if is_python_source_code_changed(self.init_framework_changes, current_framework_changes):
            LOGGER.info('framework python source code changed: reload now')
            return True
        self.init_app_base_version = current_app_base_version
        self.init_app_changes = current_app_changes
        self.init_framework_base_version = current_framework_base_version
        self.init_framework_changes = current_framework_changes
        return False


def is_python_source_code_changed(init_changes, current_changes):
    init_change_set = set(init_changes.items())
    current_change_set = set(current_changes.items())
    diff_change_set = init_change_set ^ current_change_set
    for file, version in diff_change_set:
        if '.py' in file:
            return True
    if diff_change_set:
        LOGGER.info('file changed, but not python source code')
    return False


def load_components(components):
    before = time.time()
    for component in components:
        try:
            __import__(component)
        except:
            LOGGER.exception('failed to load component: %(component)s', {
                'component': component
            })
            return False
    after = time.time()
    LOGGER.info('all components loaded: took %(elapsed_seconds)s seconds', {
        'elapsed_seconds': after - before
    })
    return True