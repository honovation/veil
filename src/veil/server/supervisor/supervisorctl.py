from __future__ import unicode_literals, print_function, division
import logging
from veil.environment import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)


def supervisorctl(action, *arguments, **kwargs):
    return shell_execute('veil execute supervisorctl -c {} {} {}'.format(VEIL_ETC_DIR / 'supervisor.cfg', action, ' '.join(arguments)), **kwargs)


def is_supervisord_running():
    try:
        import supervisor
    except:
        return False
    if not (VEIL_ETC_DIR / 'supervisor.cfg').exists():
        return False
    try:
        output = shell_execute('veil execute supervisorctl -c {} {}'.format(VEIL_ETC_DIR / 'supervisor.cfg', 'status'), capture=True)
    except Exception as e:
        if isinstance(e, ShellExecutionError) and 'SHUTDOWN_STATE' in e.output:
            return True
        LOGGER.exception('Exception occurred while checking if supervisord is running')
        return True
    else:
        return 'refused' not in output


def are_all_supervisord_programs_running():
    return all(not line or 'RUNNING' in line for line in supervisorctl('status', capture=True).splitlines(False))
