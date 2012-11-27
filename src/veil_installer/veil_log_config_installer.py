from __future__ import unicode_literals, print_function, division
from .installer import composite_installer
from .filesystem_installer import file_resource

@composite_installer
def veil_log_config_resource(path, loggers):
    content = '\n'.join(['{}={}'.format(k, v) for k, v in loggers.items()])
    return [file_resource(path=path, content=content)]