from __future__ import unicode_literals, print_function, division
import logging
from veil_installer import *
from veil.environment import *
from veil.utility.setting import *

LOGGER = logging.getLogger(__name__)

@composite_installer
def supervisor_resource(programs, inet_http_server_port=None, program_groups=None):
    inet_http_server_config = {
        'inet_http_server': {
            'host': 'localhost',
            'port': inet_http_server_port or (9091 if 'test' == VEIL_SERVER else 9090)
        }
    }
    logging_config = {
        'logging': {
            'directory': VEIL_LOG_DIR
        }
    }
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        python_package_resource(name='supervisor'),
        file_resource(path=VEIL_ETC_DIR / 'supervisor.cfg', content=render_config('supervisord.cfg.j2',
            config=merge_multiple_settings(
                inet_http_server_config,
                logging_config, {
                    'programs': programs,
                    'program_groups': program_groups,
                    'pid_file': VEIL_VAR_DIR / 'supervisor.pid'
                })
        )),
        directory_resource(path=VEIL_LOG_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP)
    ])
    return resources