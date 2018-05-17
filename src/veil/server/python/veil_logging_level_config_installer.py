from __future__ import unicode_literals, print_function, division

from veil.environment import CURRENT_USER, CURRENT_USER_GROUP
from veil_installer import *
from veil.server.os import *


@composite_installer
def veil_logging_level_config_resource(path, logging_levels):
    content = '\n'.join('{}={}'.format(k, v) for k, v in logging_levels.items())
    return [file_resource(path=path, content=content, owner=CURRENT_USER, group=CURRENT_USER_GROUP)]