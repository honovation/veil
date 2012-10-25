from __future__ import unicode_literals, print_function, division
from veil.environment.setting import *
from veil.backend.shell import *

def supervisorctl(action, *arguments):
    shell_execute('veil execute supervisorctl -c {} {} {}'.format(
        get_option('config_file'), action, ' '.join(arguments)))


def get_option(key):
    return get_settings()['supervisor'][key]