from __future__ import unicode_literals, print_function, division
import threading
from veil.frontend.cli import *
from veil.environment.supervisor import *
from veil.environment.setting import *

@script('reload')
def reload():
    settings = merge_settings(supervisor_settings(), get_settings(), overrides=True)
    restart_targets(list_targets(settings.supervisor))


def list_targets(config):
    targets = set()
    for group_name in config.groups:
        if group_name.endswith('_workers'):
            targets.add('{}:'.format(group_name))
    for program_name, program in config.programs.items():
        if program.get('group'):
            continue # grouped program will be restarted part of the group
        if program_name.endswith('_website'):
            targets.add(program_name)
    return targets


def restart_targets(targets):
    threads = []
    for target in targets:
        thread = threading.Thread(None, lambda target: supervisorctl('restart', target), args=(target,))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()