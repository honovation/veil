from __future__ import unicode_literals, print_function, division
import contextlib
import functools
import itertools
import sys
import traceback
from veil.component import get_loading_component
from veil.component import get_component_dependencies
from veil.component import get_loaded_components
from veil.component import get_transitive_dependencies
from veil.backend.shell import *
from veil.environment import *
from veil.frontend.cli import *
from .filesystem import create_directory

VEIL_INSTALLED_TAG_DIR = as_path('/tmp/veil-installed')

@script('install-all')
def install_all():
    with require_component_only_install_once():
        for component_name in get_loaded_components():
            install_dependency(component_name)


@contextlib.contextmanager
def require_component_only_install_once():
    VEIL_INSTALLED_TAG_DIR.rmtree()
    create_directory(VEIL_INSTALLED_TAG_DIR)
    try:
        yield
    finally:
        VEIL_INSTALLED_TAG_DIR.rmtree()

# create basic layout before deployment
def installation_script():
    decorator = script('install')

    def decorate(func):
        component_name = get_loading_component().__name__

        @functools.wraps(func)
        def wrapper(*argv):
            try:
                if VEIL_INSTALLED_TAG_DIR.exists():
                    installed_tag = VEIL_INSTALLED_TAG_DIR / '{}-{}'.format(component_name, '-'.join(argv))
                    if (installed_tag).exists():
                        return None
                    else:
                        (installed_tag).write_text('True')
                if os.getenv('VEIL_INSTALLATION_SCRIPT_JUST_DO_IT'):
                    return func(*argv)
                if '--print-dependencies' in argv:
                    print_dependencies(component_name)
                    return None
                create_layout()
                for dependency in get_transitive_dependencies(component_name):
                    install_dependency(dependency)
                env = os.environ.copy()
                env['VEIL_INSTALLATION_SCRIPT_JUST_DO_IT'] = 'TRUE'
                shell_execute('veil {} install {}'.format(' '.join(to_cli_handler_levels(component_name)), ' '.join(argv)), env=env)
                return None
            except:
                print('Failed to install {}'.format(component_name))
                traceback.print_exc()
                sys.exit(1)

        return decorator(wrapper)

    return decorate


def install_dependency(component_name):
    args = to_cli_handler_levels(component_name)
    args.append('install')
    if is_script_defined(*args):
        env = os.environ.copy()
        env['VEIL_INSTALLATION_SCRIPT_JUST_DO_IT'] = 'TRUE'
        shell_execute('veil {}'.format(' '.join(args)), env=env)


def to_cli_handler_levels(component_name):
    args = list(component_name.split('.'))
    if args and 'veil' == args[0]:
        args = args[1:]
    args = [arg.replace('_', '-') for arg in args]
    return args


def print_dependencies(component_name, dependencies=None, tabs_count=0):
    dependencies = dependencies or set()
    print('{}{}-{}'.format(''.join(itertools.repeat('    ', tabs_count)), tabs_count, component_name))
    for dependency in get_component_dependencies().get(component_name, ()):
        if dependency not in dependencies:
            dependencies.add(dependency)
            print_dependencies(dependency, dependencies, tabs_count + 1)


def create_layout():
    create_directory(VEIL_HOME / 'log')
    create_directory(VEIL_LOG_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP)
    create_directory(VEIL_HOME / 'etc')
    create_directory(VEIL_ETC_DIR)
    create_directory(VEIL_HOME / 'var')
    create_directory(VEIL_VAR_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP)