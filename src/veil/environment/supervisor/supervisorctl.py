from __future__ import unicode_literals, print_function, division
from veil.environment.setting import *
from veil.backend.shell import *
from .supervisor_setting import supervisor_settings

def supervisorctl(action, *arguments):
    shell_execute('veil execute supervisorctl -c {} {} {}'.format(
        get_option('config_file'), action, ' '.join(arguments)))


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


def get_option(key):
    settings = merge_settings(supervisor_settings(), get_settings(), overrides=True)
    return settings['supervisor'][key]