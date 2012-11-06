from __future__ import unicode_literals, print_function, division
from veil.environment.program_installer import *
from veil.environment.setting import *
from veil.frontend.template import *
from veil_installer import python_package_resource
from veil_installer import file_resource

@program_installer('resweb')
def install_resweb(dry_run_result):
    settings = get_settings()
    resources = [
        python_package_resource('resweb'),
        file_resource(settings.resweb.config_file, content=get_template('resweb.cfg.j2').render(
            queue_config=settings.queue_redis,
            config=settings.resweb))
    ]
    return [], resources