from __future__ import unicode_literals, print_function, division
import discipline_coach
import logging
import os
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.shell import *
from veil.development.live_document import check_live_document
from veil.development.test import check_correctness
from veil_component import check_static_dependency_integrity
from veil_component import check_static_dependency_cycle
from .encapsulation_checker import check_encapsulation
from .loc_checker import check_loc
from .logger_checker import check_logger
from .html_checker import check_html

LOGGER = logging.getLogger(__name__)

SELF_CHECKERS = {
    'dep-static-integrity': check_static_dependency_integrity,
    'dep-static-cycle': check_static_dependency_cycle,
    'encapsulation': check_encapsulation,
    'loc': check_loc,
    'live-document': check_live_document,
    'correctness': check_correctness,
    'logger': check_logger,
    'html': check_html,
}

@script('self-check')
def self_check():
    if 0 == os.getuid():
        raise Exception('self-check can not be executed using root privilege')
    shell_execute('sudo echo self-checking ...')
    shell_execute('git add -A .')
    shell_execute('git add -A .', cwd=VEIL_FRAMEWORK_HOME)
    shell_execute('veil pull')
    shell_execute('sudo veil :test down')
    shell_execute('sudo veil install-server --upgrade-mode=fast')
    shell_execute('sudo veil :test install-server --upgrade-mode=fast')
    shell_execute('sudo veil :test up --daemonize')
    shell_execute('veil quick-check')


@script('quick-check')
def quick_check(checker_name=None):
    if checker_name:
        SELF_CHECKERS[checker_name]()
        return
    shell_execute('git add -A .')
    shell_execute('git add -A .', cwd=VEIL_FRAMEWORK_HOME)
    shell_execute('veil migrate')
    for checker_name, self_checker in SELF_CHECKERS.items():
        LOGGER.info('[CHECK] checking: %(checker_name)s...', {
            'checker_name': checker_name
        })
        self_checker()
    (VEIL_HOME / '.self-check-passed').write_text(discipline_coach.calculate_git_status_hash())