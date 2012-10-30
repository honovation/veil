from __future__ import unicode_literals, print_function, division
import veil.component
import types
import os
import logging
import time
from .reloader import reload
from veil.frontend.cli import *

LOGGER = logging.getLogger(__name__)
modify_times = {}

@script('source-code-monitor-up')
def bring_up_source_code_monitor():
    while True:
        reload_on_change()


def reload_on_change():
    modified_path = is_source_code_modified()
    if modified_path:
        print('{} modified, reloading...'.format(modified_path))
        refresh_modify_times()
        reload()
    else:
        time.sleep(0.5)


def refresh_modify_times():
    modify_times.clear()
    is_source_code_modified()


def is_source_code_modified():
    for module_name, module in veil.component.force_get_all_loaded_modules().items():
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