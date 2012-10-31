from __future__ import unicode_literals, print_function, division
import contextlib
import functools
import itertools
import sys
import os
import traceback
import veil_component
from veil.backend.shell import *
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.path import *
from .filesystem import create_directory

VEIL_INSTALLED_TAG_DIR = as_path('/tmp/veil-installed')

@script('install-all')
def install_all():
    with require_component_only_install_once():
        for component_name in veil_component.get_loaded_components():
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
def installation_script(command='install'):
    decorator = script(command)

    def decorate(func):
        component_name = veil_component.get_loading_component().__name__
        veil_component.assert_module_is_must_load(func.__module__)

        @functools.wraps(func)
        def wrapper(*argv):
            try:
                if '--print-dependencies' in argv:
                    print_dependencies(component_name)
                    return None
                if VEIL_INSTALLED_TAG_DIR.exists() and is_installer_executed(component_name, command, argv):
                    return None
                if os.getenv('VEIL_INSTALLATION_SCRIPT_JUST_DO_IT'):
                    if VEIL_INSTALLED_TAG_DIR.exists():
                        mark_installer_as_executed(component_name, command, argv)
                    print('[INSTALL] executing installer {} {} {}...'.format(component_name, command, argv))
                    return func(*argv)
                create_layout()
                for dependency in veil_component.get_transitive_dependencies(component_name):
                    install_dependency(dependency)
                env = os.environ.copy()
                env['VEIL_INSTALLATION_SCRIPT_JUST_DO_IT'] = 'TRUE'
                shell_execute('veil {} {} {}'.format(
                    ' '.join(to_cli_handler_levels(component_name)), command, ' '.join(argv)),
                    env=env)
                return None
            except:
                print('Failed to install {}'.format(component_name))
                traceback.print_exc()
                sys.exit(1)

        return decorator(wrapper)

    return decorate




def is_installer_executed(component_name, command, argv):
    installer_name = '{}-{}-{}'.format(component_name, command, '-'.join(argv))[:100]
    installed_tag = VEIL_INSTALLED_TAG_DIR / installer_name
    executed = installed_tag.exists()
    if executed:
        print('[INSTALL] skip installer {}'.format(installer_name))
    return executed


def mark_installer_as_executed(component_name, command, argv):
    installer_name = '{}-{}-{}'.format(component_name, command, '-'.join(argv))[:100]
    installed_tag = VEIL_INSTALLED_TAG_DIR / installer_name
    installed_tag.write_text('True')


def install_dependency(component_name, install_dependencies_of_dependency=False):
    args = to_cli_handler_levels(component_name)
    args.append('install')
    if is_script_defined(*args):
        env = os.environ.copy()
        if install_dependencies_of_dependency:
            del env['VEIL_INSTALLATION_SCRIPT_JUST_DO_IT']
        else:
            env['VEIL_INSTALLATION_SCRIPT_JUST_DO_IT'] = 'TRUE'
        if not is_installer_executed(component_name, 'install', []):
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
    for dependency in veil_component.get_component_dependencies().get(component_name, ()):
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