from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.utility.path import *
from veil.frontend.template import *
from veil.environment import *
from veil.environment.setting import *

@composite_installer('nginx')
@using_isolated_template
def install_nginx(dry_run_result):
    settings = get_settings()
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        os_package_resource('nginx-extras'),
        os_service_resource(state='not_installed', name='nginx', path='/etc/rc0.d/K20nginx'),
        directory_resource(settings.nginx.log_directory, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        file_resource(settings.nginx.config_file, get_template('nginx.conf.j2').render(config=settings.nginx))
    ])
    uploaded_files_directory = as_path(settings.nginx.uploaded_files_directory)
    resources.append(directory_resource(
        uploaded_files_directory,
        owner=settings.nginx.owner,
        group=settings.nginx.owner_group,
        mode=0770))
    for i in range(10):
        resources.append(directory_resource(
            uploaded_files_directory / str(i),
            owner=settings.nginx.owner,
            group=settings.nginx.owner_group,
            mode=0770))
    return [], resources
