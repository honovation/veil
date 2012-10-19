from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.installation import *
from veil.environment.setting import *
from veil.frontend.template import *
from veil.frontend.cli import *
from ..queue_installer import install_queue_api

def resweb_program():
    return {
        'execute_command': 'resweb',
        'install_command': 'veil backend queue install-resweb',
        'environment_variables': {
            'RESWEB_SETTINGS': VEIL_ETC_DIR / 'resweb.cfg'
        }
    }


@script('install-resweb')
def install_queue_server():
    settings = get_settings()
    install_queue_api()
    install_python_package('resweb')
    create_file(settings.resweb.config_file, content=get_template('resweb.cfg.j2').render(
        queue_config=settings.queue_redis,
        config=settings.resweb))