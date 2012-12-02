from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

COLLECTD_CONF_PATH = VEIL_ETC_DIR / 'collectd.conf'

def collectd_program(config):
    return objectify({
        'collectd': {
            'execute_command': 'collectd -f -C {}'.format(COLLECTD_CONF_PATH),
            'redirect_stderr': False,
            'resources': [('veil.backend.collectd.collectd_resource', {
                'config': config
            })]
        }
    })