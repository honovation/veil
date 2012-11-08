from __future__ import unicode_literals, print_function, division
from veil.environment.setting import *
from veil.backend.shell import *
from veil.environment.supervisor_setting import supervisor_settings

def supervisorctl(action, *arguments, **kwargs):
    return shell_execute('veil execute supervisorctl -c {} {} {}'.format(
        get_option('config_file'), action, ' '.join(arguments)), **kwargs)


def is_supervisord_running():
    try:
        import supervisor
    except:
        return False
    try:
        output = shell_execute('veil execute supervisorctl -c {} {}'.format(
            get_option('config_file'), 'status'), capture=True)
        return 'refused' not in output
    except ShellExecutionError, e:
        if 'SHUTDOWN_STATE' in e.output:
            return True
        raise

def are_all_supervisord_programs_running():
    for line in supervisorctl('status', capture=True).split('\n'):
        if line and 'RUNNING' not in line:
            return False
    return True


def get_option(key):
    settings = merge_settings(supervisor_settings(), get_settings(), overrides=True)
    return settings['supervisor'][key]