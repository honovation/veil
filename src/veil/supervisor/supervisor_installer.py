from __future__ import unicode_literals, print_function, division
from veil.frontend.template import *
from veil.frontend.cli import *
from veil.environment import *
from veil.environment.setting import *
from veil.environment.installation import *
from .supervisor_setting import supervisor_settings

@script('install')
def install_veil():
    with require_component_only_install_once():
        import __veil__

        program_installers = getattr(__veil__, 'PROGRAM_INSTALLERS', {})
        if VEIL_SERVER in ['development', 'test']:
            for program_installer in program_installers.values():
                program_installer()
            install_supervisor()
        else:
            active_programs = getattr(__veil__, 'ENVIRONMENTS', {})[VEIL_ENV][VEIL_ENV_SERVER]
            for program in active_programs:
                program_installers[program]()
            install_supervisor(*active_programs)


def install_supervisor(*active_programs):
    settings = merge_settings(supervisor_settings(), get_settings(), overrides=True)
    config = settings.supervisor
    all_programs = config.programs.keys()
    if VEIL_ENV in ['development', 'test']:
        active_programs = all_programs
    else:
        if not active_programs:
            return
    install_python_package('supervisor')
    create_file(config.config_file, get_template('supervisord.cfg.j2').render(
        config=config,
        active_programs=active_programs,
        CURRENT_USER=CURRENT_USER,
        format_command=format_command,
        format_environment_variables=format_environment_variables
    ))
    create_directory(config.logging.directory, owner=CURRENT_USER, group=CURRENT_USER_GROUP)


def format_command(command, args):
    return get_template(template_source=command).render(**args or {})


def format_environment_variables(environment_variables):
    return ','.join(['{}={}'.format(k, v) for k, v in environment_variables.items()])