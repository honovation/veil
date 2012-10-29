from __future__ import unicode_literals, print_function, division
import logging
import veil.component

veil.component.add_must_load_module(__name__)

from veil.frontend.template import *
from veil.frontend.cli import *
from veil.backend.shell import *
from veil.environment import *
from veil.environment.setting import *
from veil.environment.installation import *
from .supervisor_setting import supervisor_settings

LOGGER = logging.getLogger(__name__)

@script('install-programs')
def install_programs():
    settings = merge_settings(supervisor_settings(), get_settings(), overrides=True)
    config = settings.supervisor
    assert_programs_loaded(config.programs.values())
    with require_component_only_install_once():
        import __veil__

        if VEIL_SERVER in ['development', 'test']:
            print('[INSTALL] about to install programs {} ...'.format(config.programs.keys()))
            for program_name, program in config.programs.items():
                print('[INSTALL] installing program {} ...'.format(program_name))
                install_program(program)
            shell_execute('veil environment supervisor install {}'.format(' '.join(config.programs.keys())))
        else:
            server = get_current_veil_server()
            print('[INSTALL] about to install programs {} ...'.format(server.programs))
            for program_name in server.programs:
                print('[INSTALL] installing program {} ...'.format(program_name))
                install_program(config.programs[program_name])
            shell_execute('veil environment supervisor install {}'.format(' '.join(server.programs)))

def assert_programs_loaded(programs):
    for program in programs:
        assert not veil.component.is_dummy_module_member(program), 'program is not loaded properly: {}'.format(program)


def install_program(program):
    install_command = getattr(program, 'install_command', None)
    if install_command:
        shell_execute(install_command)


@installation_script()
def install_supervisor(*active_program_names):
    settings = merge_settings(supervisor_settings(), get_settings(), overrides=True)
    config = settings.supervisor
    if not active_program_names:
        return
    install_python_package('supervisor')
    create_file(config.config_file, get_template('supervisord.cfg.j2').render(
        config=config,
        active_program_names=active_program_names,
        CURRENT_USER=CURRENT_USER,
        format_command=format_command,
        format_environment_variables=format_environment_variables
    ))
    create_directory(config.logging.directory, owner=CURRENT_USER, group=CURRENT_USER_GROUP)


def format_command(program, args):
    try:
        return get_template(template_source=program.execute_command).render(**args or {})
    except:
        LOGGER.error('Failed to format command for: {}'.format(program))
        raise


def format_environment_variables(environment_variables):
    return ','.join(['{}={}'.format(k, v) for k, v in environment_variables.items()])