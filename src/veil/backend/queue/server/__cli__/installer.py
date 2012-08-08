from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.environment.deployment import *
from veil.frontend.template import *


@deployment_script('install')
def install_queue_server():
    settings = get_deployment_settings()
    install_ubuntu_package('python2.7-dev')
    execute_script('backend', 'redis', 'client', 'install')
    execute_script('backend', 'redis', 'server', 'install', 'queue')
    install_python_package('pytz')
    install_python_package('pyres')
    install_python_package('croniter')
    install_python_package('resweb')
    create_file(settings.resweb.config_file, content=get_template('resweb.cfg.j2').render(
        queue_config=settings.queue,
        config=settings.resweb))