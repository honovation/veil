from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

LOGGER = logging.getLogger(__name__)


@composite_installer
def supervisor_resource(programs, inet_http_server_host=None, inet_http_server_port=None, program_groups=None):
    inet_http_server_config = {
        'inet_http_server': {
            'host': inet_http_server_host or '*',
            'port': inet_http_server_port or (9091 if VEIL_ENV.is_test else 9090)
        }
    }
    logging_config = {
        'logging': {
            'directory': VEIL_LOG_DIR
        }
    }
    return [
        python_package_resource(name='supervisor'),
        file_resource(path=VEIL_ETC_DIR / 'supervisor.cfg',
                      content=render_config('supervisord.cfg.j2',
                                            config=merge_multiple_settings(inet_http_server_config, logging_config,
                                                                           dict(programs=programs, program_groups=program_groups or {},
                                                                                pid_file='/tmp/supervisor.pid')))),
        directory_resource(path=VEIL_LOG_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP)
    ]
