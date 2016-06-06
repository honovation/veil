from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

_config = {}

add_application_sub_resource('yto_client', lambda config: yto_client_resource(**config))


@composite_installer
def yto_client_resource(**kwargs):
    return [
        file_resource(path=VEIL_ETC_DIR / 'yto-client-{}.cfg'.format(purpose),
                      content=render_config('yto-client.cfg.j2', api_url=purpose_config.api_url, type=purpose_config.type, client_id=purpose_config.client_id,
                                            partner_id=purpose_config.partner_id))
        for purpose, purpose_config in kwargs.items()
    ]


def load_yto_client_config(purpose):
    return load_config_from(VEIL_ETC_DIR / 'yto-client-{}.cfg'.format(purpose), 'api_url', 'client_id', 'type', 'partner_id')


def yto_client_config(purpose=None):
    purpose = purpose or ('test' if VEIL_ENV_TYPE != 'public' else 'public')
    global _config
    if not _config.get(purpose):
        _config[purpose] = load_yto_client_config(purpose)
    return _config[purpose]
