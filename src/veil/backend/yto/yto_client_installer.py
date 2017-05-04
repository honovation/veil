from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *
from veil.environment import VEIL_BUCKET_LOG_DIR

YTO_INCOMING_REQUEST_LOG_DIRECTORY_BASE = VEIL_BUCKET_LOG_DIR / 'yto/incoming/request'

_config = {}


@composite_installer
def yto_client_resource(**kwargs):
    resources = [
        file_resource(path=VEIL_ETC_DIR / 'yto-client-{}.cfg'.format(purpose),
                      content=render_config('yto-client.cfg.j2', api_url=purpose_config.api_url, type=purpose_config.type, client_id=purpose_config.client_id,
                                            partner_id=purpose_config.partner_id))
        for purpose, purpose_config in kwargs.items()
    ]
    resources.append(directory_resource(path=YTO_INCOMING_REQUEST_LOG_DIRECTORY_BASE, owner=CURRENT_USER, group=CURRENT_USER_GROUP, recursive=True))
    return resources


def load_yto_client_config(purpose):
    return load_config_from(VEIL_ETC_DIR / 'yto-client-{}.cfg'.format(purpose), 'api_url', 'client_id', 'type', 'partner_id')


def yto_client_config(purpose=None):
    purpose = purpose or (VEIL_ENV.type if VEIL_ENV.is_prod else 'test')
    global _config
    if not _config.get(purpose):
        _config[purpose] = load_yto_client_config(purpose)
    return _config[purpose]
