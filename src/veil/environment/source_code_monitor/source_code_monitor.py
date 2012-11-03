from __future__ import unicode_literals, print_function, division
import veil_component
import types
import os
import logging
import time
import sys
from .reloader import reload
from veil.environment import *
from veil.frontend.cli import *

LOGGER = logging.getLogger(__name__)
modify_times = {}

def source_code_monitor_settings():
    if 'development' != VEIL_SERVER:
        return {}
    return {
        'supervisor': {
            'programs': {
                'source_code_monitor': {
                    'execute_command': 'veil environment source-code-monitor up',
                    'startsecs': 0
                }
            }
        }
    }


@script('up')
def bring_up_source_code_monitor():
    LOGGER.info('start monitoring source code changes...')
    while True:
        reload_on_change()


def reload_on_change(exit_on_no_change=False):
    modified_path = is_source_code_modified()
    if modified_path:
        LOGGER.info('{} modified, reloading...'.format(modified_path))
        refresh_modify_times()
        reload()
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