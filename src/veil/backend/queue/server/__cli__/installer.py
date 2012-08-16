from __future__ import unicode_literals, print_function, division
from veil.environment.installation import *
from veil.environment.setting import *
from veil.frontend.template import *
from veil.backend.shell import *


@installation_script()
def install_queue_server():
    shell_execute('veil backend redis server install queue')
    settings = get_settings()
    install_ubuntu_package('python2.7-dev')
    install_python_package('pytz')
    install_python_package('pyres')
    install_python_package('croniter')
    install_python_package('resweb')
    create_file(settings.resweb.config_file, content=get_template('resweb.cfg.j2').render(
        queue_config=settings.queue,
        config=settings.resweb))