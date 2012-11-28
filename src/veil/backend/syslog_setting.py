from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment import *

def syslog_server_program(config):
    return objectify({
        'syslog_server': {
            'execute_command': 'syslog-ng --no-caps --user={} --foreground --cfgfile={} --persist-file={} --pidfile={}'.format(
                CURRENT_USER, VEIL_ETC_DIR / 'syslog-ng.conf',
                VEIL_VAR_DIR / 'syslog-ng.persist',
                VEIL_VAR_DIR / 'syslog-ng.pid'),
            'resources': [('veil.backend.syslog.syslog_server_resource', {'config': config})]
        }
    })