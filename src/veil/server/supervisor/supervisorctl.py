from __future__ import unicode_literals, print_function, division
import logging
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)


@script('reload-nginx')
def reload_nginx(program_name='nginx'):
    supervisorctl('signal', 'HUP', program_name, capture=True)
    prime_nginx_ocsp_cache()


@script('prime-nginx-ocsp-cache')
def prime_nginx_ocsp_cache():
    config_path = VEIL_ETC_DIR / 'nginx-https.cfg'
    if not config_path.exists():
        return
    for line in config_path.text().splitlines():
        server_name, https_ports = line.split(':')
        port = https_ports.split(',')[0]
        cmd = 'nohup openssl s_client -connect {0}:{1} -servername {0} -status >/dev/null 2>&1 &'.format(server_name,
                                                                                                         port)
        try:
            shell_execute(cmd, capture=True)
        except:
            LOGGER.warn('Exception occurred while priming nginx ocsp cache: {}'.format(cmd), exc_info=1)


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
