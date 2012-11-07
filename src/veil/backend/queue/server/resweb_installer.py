from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.frontend.template import *
from veil_installer import *

@installer('resweb')
@using_isolated_template
def install_resweb(dry_run_result):
    settings = get_settings()
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        python_package_resource('resweb'),
        file_resource(settings.resweb.config_file, content=get_template('resweb.cfg.j2').render(
            queue_config=settings.queue_redis,
            config=settings.resweb))
    ])
    return [], resources