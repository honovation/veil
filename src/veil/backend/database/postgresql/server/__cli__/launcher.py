from __future__ import unicode_literals, print_function, division
import contextlib
import time
from veil.frontend.cli import *
from veil.backend.shell import *
from veil.environment.setting import *

@script('up')
def bring_up_postgresql_server(purpose='postgresql'):
    settings = get_settings()
    config = getattr(settings, purpose)
    pass_control_to('postgres -D {}'.format(config.data_directory))


@script('down')
def bring_down_postgresql_server(purpose='postgresql', config=None):
    settings = get_settings()
    config = config or getattr(settings, purpose)
    shell_execute('su {} -c "pg_ctl -D {} stop"'.format(
        config.owner, config.data_directory))


@contextlib.contextmanager
def postgresql_server_running(config):
    shell_execute('su {} -c "pg_ctl -D {} start"'.format(
        config.owner, config.data_directory))
    time.sleep(5)
    yield
    bring_down_postgresql_server(config=config)