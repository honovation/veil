from __future__ import unicode_literals, print_function, division
import discipline_coach
import logging
from veil.frontend.cli import *
from veil.environment import *
from veil.utility.shell import *
from veil.development.live_document import check_live_document
from veil.development.test import check_correctness
from veil.backend.database.postgresql import check_if_locked_migration_scripts_being_changed
from .architecture_checker import check_architecture
from .encapsulation_checker import check_encapsulation
from .loc_checker import check_loc
from .logger_checker import check_logger

LOGGER = logging.getLogger(__name__)

SELF_CHECKERS = {
    'architecture': check_architecture,
    'encapsulation': check_encapsulation,
    'loc': check_loc,
    'live-document': check_live_document,
    'correctness': check_correctness,
    'migration-scripts': check_if_locked_migration_scripts_being_changed,
    'logger': check_logger
}

@script('self-check')
def self_check():
    shell_execute('git add .')
    shell_execute('veil pull')
    quick_check()


@script('quick-check')
def quick_check(checker_name=None):
    for component_name in get_application_components():
        __import__(component_name) # check if all components can be loaded
    if checker_name:
        SELF_CHECKERS[checker_name]()
        return
    shell_execute('git add .')
    shell_execute('veil migrate')
    for checker_name, self_checker in SELF_CHECKERS.items():
        LOGGER.info('[CHECK] checking {}...'.format(checker_name))
        self_checker()
    (VEIL_HOME / '.self-check-passed').write_text(discipline_coach.calculate_git_status_hash())