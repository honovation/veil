from __future__ import unicode_literals, print_function, division
import logging
import threading
import functools
from veil.frontend.cli import *
from veil.utility.shell import *
from veil.environment import *
from veil_installer import *

LOGGER = logging.getLogger(__name__)

@script('deploy')
def deploy():
    assert_no_local_change(VEIL_FRAMEWORK_HOME)
    assert_no_local_change(VEIL_HOME)
    shell_execute('veil install veil_installer.component_resource?veil.server.supervisor --upgrade-mode={}'.format(UPGRADE_MODE_FAST))
    shell_execute('veil down')
    shell_execute('veil install-server --upgrade-mode={}'.format(UPGRADE_MODE_FAST))
    shell_execute('veil up --daemonize')
    shell_execute('veil migrate')
    assert_no_local_change(VEIL_FRAMEWORK_HOME)
    assert_no_local_change(VEIL_HOME)


def assert_no_local_change(dir_):
    output = shell_execute('git status -s', cwd=dir_, capture=True)
    if output:
        raise Exception('Local change detected:\n{}'.format(output))


@script('patch')
def patch():
    shell_execute('veil migrate')
    threads = []
    for program_name, program in get_current_veil_server().programs.items():
        if program.get('patchable'):
            program_name = '{}:{}'.format(program['group'], program_name) if program.get('group') else program_name
            thread = threading.Thread(target=functools.partial(shell_execute, 'veil server supervisor restart-program {}'.format(program_name)))
            threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()