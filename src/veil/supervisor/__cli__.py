from __future__ import unicode_literals, print_function, division
from veil.backend.shell import *
from veil.frontend.template import *
from veil.environment import *
from veil.environment.setting import *
from veil.environment.installation import *
from veil.frontend.cli import script

@installation_script()
def install_supervisor():
    settings = get_settings()
    install_python_package('supervisor')
    create_file(settings.supervisor.config_file, get_template('supervisord.cfg.j2').render(
        config=settings.supervisor,
        CURRENT_USER=CURRENT_USER,
        format_command=format_command,
        format_environment_variables=format_environment_variables
    ))
    create_directory(settings.supervisor.logging.directory)


@script('up')
def bring_up_supervisor():
    settings = get_settings()
    pass_control_to('supervisord -c {}'.format(settings.supervisor.config_file))


def format_command(command, args):
    return get_template(template_source=command).render(**args or {})


def format_environment_variables(environment_variables):
    return ','.join(['{}={}'.format(k, v) for k, v in environment_variables.items()])