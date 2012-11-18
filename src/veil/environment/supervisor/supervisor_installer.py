from __future__ import unicode_literals, print_function, division
import logging
from veil_installer import *
from veil.frontend.template import *
from veil.environment import *
from veil.environment.setting import *

LOGGER = logging.getLogger(__name__)

@composite_installer('supervisor')
@using_isolated_template
def install_supervisor(programs, inet_http_server_host=None, inet_http_server_port=None):
    if inet_http_server_host and inet_http_server_port:
        inet_http_server_config = {
            'inet_http_server': {
                'host': inet_http_server_host,
                'port': inet_http_server_port
            }
        }
    else:
        inet_http_server_config = {}
    logging_config = {
        'logging': {
            'directory': VEIL_LOG_DIR
        }
    }
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        python_package_resource('supervisor'),
        file_resource(VEIL_ETC_DIR / 'supervisor.cfg', get_template('supervisord.cfg.j2').render(
            config=merge_multiple_settings(
                inet_http_server_config,
                logging_config, {
                    'programs': programs,
                    'pid_file': VEIL_VAR_DIR / 'supervisor.pid'
                })
        )),
        directory_resource(VEIL_LOG_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP)
    ])
    return [], resources