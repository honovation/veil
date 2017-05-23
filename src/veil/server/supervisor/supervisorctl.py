from __future__ import unicode_literals, print_function, division
import logging
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)


@script('reload-nginx')
def reload_nginx(program_name='nginx'):
    supervisorctl('signal', 'HUP', program_name, capture=True)


def supervisorctl(action, *arguments, **kwargs):
    return shell_execute(
        'supervisorctl -c {} {} {}'.format(VEIL_ETC_DIR / 'supervisor.cfg', action, ' '.join(arguments)), **kwargs)


def is_supervisord_running():
    try:
        import supervisor
    except Exception:
        return False
    if not (VEIL_ETC_DIR / 'supervisor.cfg').exists():
        return False
    try:
        output = shell_execute('supervisorctl -c {} {}'.format(VEIL_ETC_DIR / 'supervisor.cfg', 'status'), capture=True)
    except Exception as e:
        if isinstance(e, ShellExecutionError) and 'SHUTDOWN_STATE' in e.output:
            return True
        LOGGER.exception('Exception occurred while checking if supervisord is running')
        return True
    else:
        return 'pid' in output
