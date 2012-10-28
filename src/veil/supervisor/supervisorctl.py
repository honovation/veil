from __future__ import unicode_literals, print_function, division
from veil.environment.setting import *
from veil.backend.shell import *
from .supervisor_setting import supervisor_settings

def supervisorctl(action, *arguments):
    shell_execute('veil execute supervisorctl -c {} {} {}'.format(
        get_option('config_file'), action, ' '.join(arguments)))


def is_supervisord_running():
    output = shell_execute('veil execute supervisorctl -c {} {}'.format(
        get_option('config_file'), 'status'), capture=True)
    return 'refused' not in output


def get_option(key):
    settings = merge_settings(supervisor_settings(), get_settings(), overrides=True)
    return settings['supervisor'][key]