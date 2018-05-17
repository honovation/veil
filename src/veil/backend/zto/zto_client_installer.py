from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *
from veil.environment import VEIL_BUCKET_LOG_DIR

ZTO_INCOMING_REQUEST_LOG_DIRECTORY_BASE = VEIL_BUCKET_LOG_DIR / 'zto/incoming/request'

_config = {}


@composite_installer
def zto_client_resource(company_id, api_key, subscribe_create_by, subscribe_api_key):
    return [
        directory_resource(path=ZTO_INCOMING_REQUEST_LOG_DIRECTORY_BASE, owner=CURRENT_USER, group=CURRENT_USER_GROUP, recursive=True),
        file_resource(path=VEIL_ETC_DIR / 'zto-client.cfg', content=render_config('zto-client.cfg.j2', company_id=company_id, api_key=api_key,
                                                                                  subscribe_create_by=subscribe_create_by, subscribe_api_key=subscribe_api_key),
                      owner=CURRENT_USER, group=CURRENT_USER_GROUP)
    ]


def load_zto_client_config():
    return load_config_from(VEIL_ETC_DIR / 'zto-client.cfg', 'company_id', 'api_key', 'subscribe_create_by', 'subscribe_api_key')


def zto_client_config():
    global _config
    if not _config:
        _config = load_zto_client_config()
    return _config
