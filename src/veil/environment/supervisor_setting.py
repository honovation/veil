from __future__ import unicode_literals, print_function, division
from veil.environment.setting import *
from veil.environment import *
from veil.model.collection import *

def init():
    register_settings_coordinator(consolidate_program_groups)

def supervisor_settings(**updates):
    settings = {
        'programs': {},
        'config_file': VEIL_ETC_DIR / 'supervisor.cfg',
        'logging': {
            'directory': VEIL_LOG_DIR
        },
        'inet_http_server': {
            'host': '127.0.0.1',
            'port': 9090 if 'test' != VEIL_SERVER else 9091
        },
        'pid_file': VEIL_VAR_DIR / 'supervisord.pid',
        'daemonize': False if VEIL_SERVER in ['development', 'test'] else True
    }
    settings = merge_settings(settings, updates, overrides=True)
    return objectify({'supervisor': settings})

def consolidate_program_groups(settings):
    groups = {}
    for program_name, program in settings.supervisor.programs.items():
        if is_current_veil_server_hosting(program_name):
            belong_to_group = program.get('group', None)
            if belong_to_group:
                groups.setdefault(belong_to_group, set()).add(program_name)
    return merge_settings(settings, {
        'supervisor': {
            'groups': groups
        }
    })

init()