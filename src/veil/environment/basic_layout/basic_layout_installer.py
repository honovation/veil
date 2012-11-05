from __future__ import unicode_literals, print_function, division
from veil_installer import directory_resource
from veil.environment import *

def install_basic_layout(dry_run_result):
    return [], [
        directory_resource(VEIL_HOME / 'log'),
        directory_resource(VEIL_LOG_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        directory_resource(VEIL_HOME / 'etc'),
        directory_resource(VEIL_ETC_DIR),
        directory_resource(VEIL_HOME / 'var'),
        directory_resource(VEIL_VAR_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP)
    ]