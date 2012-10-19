from __future__ import unicode_literals, print_function, division
import logging
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
    with require_component_only_install_once():
        import __veil__

        if VEIL_SERVER in ['development', 'test']:
            for program in config.programs.values():
                install_program(program)
            shell_execute('veil supervisor install {}'.format(' '.join(config.programs.keys())))
        else:
            active_program_names = getattr(__veil__, 'ENVIRONMENTS', {})[VEIL_ENV][VEIL_ENV_SERVER]
            for program_name in active_program_names:
                install_program(config.programs[program_name])
            shell_execute('veil supervisor install {}'.format(' '.join(active_program_names.keys())))


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