from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.utility.shell import *

def supervisorctl(action, *arguments, **kwargs):
    return shell_execute('veil execute supervisorctl -c {} {} {}'.format(
        VEIL_ETC_DIR / 'supervisor.cfg', action, ' '.join(arguments)), **kwargs)


def is_supervisord_running():
    try:
        import supervisor
    except:
        return False
    if not (VEIL_ETC_DIR / 'supervisor.cfg').exists():
        return False
    try:
        output = shell_execute('veil execute supervisorctl -c {} {}'.format(
            VEIL_ETC_DIR / 'supervisor.cfg', 'status'), capture=True)
        return 'refused' not in output
    except ShellExecutionError, e:
        if 'SHUTDOWN_STATE' in e.output:
            return True
        raise

def are_all_supervisord_programs_running():
    for line in supervisorctl('status', capture=True).split('\n'):
        if line and 'RUNNING' not in line:
            return False
    return True