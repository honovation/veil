from __future__ import unicode_literals, print_function, division
import types
import os
import logging
import time
import sys
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.shell import *
from .reloader import restart_all
from .reloader import start_all

LOGGER = logging.getLogger(__name__)
modify_times = {}

@script('up')
def bring_up_source_code_monitor():
    for component_name in get_application_components():
        __import__(component_name)
    LOGGER.info('start monitoring source code changes...')
    shell_execute('find {} -type f -name "*.pyc" -delete'.format(VEIL_FRAMEWORK_HOME))
    shell_execute('find {} -type f -name "*.pyc" -delete'.format(VEIL_HOME))
    start_all()
    while True:
        reload_on_change()


def reload_on_change(exit_on_no_change=False):
    modified_path = is_source_code_modified()
    if modified_path:
        LOGGER.info('{} modified, reloading...'.format(modified_path))
        refresh_modify_times()
        restart_all()
        reload_on_change(exit_on_no_change=True) # refresh the state
    else:
        if exit_on_no_change:
            sys.exit(1)
        else:
            time.sleep(1)


def refresh_modify_times():
    modify_times.clear()
    is_source_code_modified()


def is_source_code_modified():
    for module_name, module in sys.modules.items():
        # Some modules play games with sys.modules (e.g. email/__init__.py
        # in the standard library), and occasionally this can cause strange
        # failures in getattr.  Just ignore anything that's not an ordinary
        # module.
        if not isinstance(module, types.ModuleType): continue
        path = getattr(module, "__file__", None)
        if not path: continue
        if path.endswith('.pyc') or path.endswith('.pyo'):
            path = path[:-1]
        try:
            modified = os.stat(path).st_mtime
        except:
            continue
        if path not in modify_times:
            modify_times[path] = modified
            continue
        if modify_times[path] != modified:
            return path