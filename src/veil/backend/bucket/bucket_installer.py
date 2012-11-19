from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.frontend.template import *
from veil.environment import *
from veil.environment.setting import *

@composite_installer('bucket')
@using_isolated_template
def install_bucket(purpose, config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(
        file_resource(VEIL_ETC_DIR / '{}-bucket.cfg'.format(purpose.replace('_', '-')), content=get_template(
            'bucket.cfg.j2').render(config=config)))
    return [], resources


def load_bucket_config(purpose):
    config = load_config_from(VEIL_ETC_DIR / '{}-bucket.cfg'.format(purpose.replace('_', '-')),
        'type', 'base_directory', 'base_url')
    return config