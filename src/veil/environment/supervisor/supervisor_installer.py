from __future__ import unicode_literals, print_function, division
import logging
from veil_installer import *
from veil.frontend.template import *
from veil.environment import *
from veil.environment.setting import *
from veil.environment.supervisor_setting import supervisor_settings

LOGGER = logging.getLogger(__name__)

@installer('supervisor')
@using_template
def install_supervisor(dry_run_result):
    settings = merge_settings(supervisor_settings(), get_settings(), overrides=True)
    config = settings.supervisor
    if VEIL_SERVER in ['development', 'test']:
        active_program_names = config.programs.keys()
    else:
        active_program_names = get_current_veil_server().programs
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        python_package_resource('supervisor'),
        file_resource(config.config_file, get_template('supervisord.cfg.j2').render(
            config=config,
            active_program_names=active_program_names,
            CURRENT_USER=CURRENT_USER,
            format_command=format_command,
            format_environment_variables=format_environment_variables
        )),
        directory_resource(config.logging.directory, owner=CURRENT_USER, group=CURRENT_USER_GROUP)
    ])
    return [], resources


def format_command(program, args):
    try:
        return get_template(template_source=program.execute_command).render(**args or {})
    except:
        LOGGER.error('Failed to format command for: {}'.format(program))
        raise


def format_environment_variables(environment_variables):
    return ','.join(['{}={}'.format(k, v) for k, v in environment_variables.items()])