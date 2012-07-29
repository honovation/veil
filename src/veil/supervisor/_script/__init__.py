from __future__ import unicode_literals, print_function, division
import jinja2
from veil.script import *
from sandal.shell import *
from sandal.template import *
from ...filesystem import create_file
from ...filesystem import create_directory
from ...python_package import install_python_package
from ...setting import get_deployment_settings

@script('install')
def install_supervisor():
    settings = get_deployment_settings()
    install_python_package('supervisor')
    create_file(settings.supervisor.config_file, get_template('supervisord.cfg.j2').render(
        config=settings.supervisor,
        format_command=format_command,
        format_environment_variables=format_environment_variables
    ))
    create_directory(settings.supervisor.logging.directory)


@script('up')
def bring_up_supervisor():
    settings = get_deployment_settings()
    pass_control_to('supervisord -c {}'.format(settings.supervisor.config_file))


def format_command(command, args):
    return jinja2.Environment().from_string(command).render(**args or {})


def format_environment_variables(environment_variables):
    return ','.join(['{}={}'.format(k, v) for k, v in environment_variables.items()])