from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.server.os import *

@composite_installer
def veil_logging_level_config_resource(path, logging_levels):
    content = '\n'.join('{}={}'.format(k, v) for k, v in logging_levels.items())
    return [file_resource(path=path, content=content)]