from __future__ import unicode_literals, print_function, division
import importlib
import discipline_coach
from veil.frontend.cli import *
from veil.environment import *
from veil.environment.setting import *
from veil.utility.shell import *

@script('self-check')
def self_check():
    shell_execute('git add .')
    shell_execute('veil pull')
    shell_execute('veil environment local-deployer reset')
    quick_check()


@script('quick-check')
def quick_check(checker_name=None):
    load_application_components()
    if checker_name:
        get_self_checkers()[checker_name]()
        return
    for checker_name, self_checker in get_self_checkers().items():
        print('[CHECK] checking {}...'.format(checker_name))
        self_checker()
    (VEIL_HOME / '.self-check-passed').write_text(discipline_coach.calculate_git_status_hash())

def get_self_checkers():
    return {k: import_self_checker(v) for k, v in get_settings()['self_checkers'].items()}

def import_self_checker(module_and_function_name):
    parts = module_and_function_name.split('.')
    module = importlib.import_module('.'.join(parts[:-1]))
    return getattr(module, parts[-1])