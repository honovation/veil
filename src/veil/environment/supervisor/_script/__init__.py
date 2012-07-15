import jinja2
from sandal.script import *
from sandal.shell import *
from sandal.option import *
from sandal.template import *
from ...file import create_file
from ...directory import create_directory
from ...layout import init_env

@script('install')
def install_supervisor():
    options = init_env()
    try:
        __import__('supervisor')
    except ImportError:
        shell_execute('pip install supervisor')
    create_file(options.supervisor.config_file, get_template('supervisord.cfg.j2').render(
        format_command=format_command,
        format_environment_variables=format_environment_variables
    ))
    create_directory(options.supervisor.logging.directory)

@script('up')
def bring_up_supervisor():
    options = init_env()
    shell_execute('supervisord -c {}'.format(options.supervisor.config_file))


def format_command(command, args):
    return jinja2.Environment().from_string(command).render(**args or {})


def format_environment_variables(environment_variables):
    return ','.join(['{}={}'.format(k, v) for k, v in environment_variables.items()])