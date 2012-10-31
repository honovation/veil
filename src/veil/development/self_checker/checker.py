from __future__ import unicode_literals, print_function, division
import discipline_coach
from veil.frontend.cli import *
from veil.environment import *
from veil.backend.shell import *

self_checkers = {}

def register_self_checker(name, self_checker):
    self_checkers[name] = self_checker


@script('self-check')
def self_check(checker_name=None):
    if checker_name:
        self_checkers[checker_name]()
        return
    for checker_name, self_checker in self_checkers.items():
        print('[CHECK] checking {}...'.format(checker_name))
        self_checker()
    shell_execute('git add .')
    (VEIL_HOME / '.self-check-passed').write_text(discipline_coach.calculate_git_status_hash())