from __future__ import unicode_literals, print_function, division
import logging
import functools
import time
import threading
import discipline_coach
import os
from veil.environment import VEIL_ENV_TYPE, VEIL_HOME, VEIL_FRAMEWORK_HOME
from veil.frontend.website_setting import list_website_components

LOGGER = logging.getLogger(__name__)


def source_code_monitored(func):
    @functools.wraps(func)
    def wrapper(*args):
        purpose = args[0]
        components = list_website_components(purpose)
        LOGGER.info('load components: %(components)s', {'components': components})
        if 'development' == VEIL_ENV_TYPE:
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
        self.init_app_base_version = None
        self.init_app_changes = None
        self.init_framework_base_version = None
        self.init_framework_changes = None
        try:
            self.init_app_base_version, self.init_app_changes = discipline_coach.get_git_dir_version(VEIL_HOME)
        except Exception:
            pass
        try:
            self.init_framework_base_version, self.init_framework_changes = discipline_coach.get_git_dir_version(VEIL_FRAMEWORK_HOME)
        except Exception:
            pass

    def run(self):
        while True:
            try:
                time.sleep(0.5)
                if self.detect_change():
                    os._exit(1)
            except Exception:
                LOGGER.exception('source code monitor died')

    def detect_change(self):
        return self.detect_app_change() or self.detect_framework_change()

    def detect_framework_change(self):
        while 1:
            try:
                current_framework_base_version, current_framework_changes = discipline_coach.get_git_dir_version(VEIL_FRAMEWORK_HOME)
            except Exception:
                pass
            else:
                if self.init_framework_base_version:
                    if self.init_framework_base_version != current_framework_base_version:
                        LOGGER.info('framework base version changed: reload now')
                        self.init_framework_base_version = current_framework_base_version
                        return True
                else:
                    self.init_framework_base_version = current_framework_base_version

                if self.init_framework_changes:
                    if is_python_source_code_changed(self.init_framework_changes, current_framework_changes):
                        LOGGER.info('framework python source code changed: reload now')
                        self.init_framework_changes = current_framework_changes
                        return True
                else:
                    self.init_framework_changes = current_framework_changes
                return False

    def detect_app_change(self):
        while 1:
            try:
                current_app_base_version, current_app_changes = discipline_coach.get_git_dir_version(VEIL_HOME)
            except Exception:
                pass
            else:
                if self.init_app_base_version:
                    if self.init_app_base_version != current_app_base_version:
                        LOGGER.info('application base version changed: reload now')
                        self.init_app_base_version = current_app_base_version
                        return True
                else:
                    self.init_app_base_version = current_app_base_version

                if self.init_app_changes:
                    if is_python_source_code_changed(self.init_app_changes, current_app_changes):
                        LOGGER.info('application python source code changed: reload now')
                        self.init_app_changes = current_app_changes
                        return True
                else:
                    self.init_app_changes = current_app_changes
                return False


def is_python_source_code_changed(init_changes, current_changes):
    init_change_set = set(init_changes.items())
    current_change_set = set(current_changes.items())
    diff_change_set = init_change_set ^ current_change_set
    for path, version in diff_change_set:
        if '.py' in path:
            return True
    if diff_change_set:
        LOGGER.info('file changed, but not python source code')
    return False


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
