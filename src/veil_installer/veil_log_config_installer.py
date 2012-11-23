from __future__ import unicode_literals, print_function, division
from veil_installer import *

@composite_installer('veil_log_config')
def install_veil_log_config(path, loggers):
    content = '\n'.join(['{}={}'.format(k, v) for k, v in loggers.items()])
    return [], [file_resource(path, content)]


def veil_log_config_resource(path, loggers):
    return ('veil_log_config', {
        'path': path,
        'loggers': loggers
    })