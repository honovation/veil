from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *

@composite_installer('nginx')
def install_nginx(servers):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        os_package_resource('nginx-extras'),
        os_service_resource(state='not_installed', name='nginx', path='/etc/rc0.d/K20nginx'),
        directory_resource(VEIL_LOG_DIR / 'nginx', owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        file_resource(VEIL_ETC_DIR / 'nginx.conf', render_config('nginx.conf.j2', config={
            'owner': CURRENT_USER,
            'owner_group': CURRENT_USER_GROUP,
            'log_directory': VEIL_LOG_DIR / 'nginx',
            'servers': servers
        }))
    ])
    uploaded_files_directory = VEIL_VAR_DIR / 'uploaded-files'
    resources.append(directory_resource(
        uploaded_files_directory,
        owner=CURRENT_USER,
        group=CURRENT_USER_GROUP,
        mode=0770))
    for i in range(10):
        resources.append(directory_resource(
            uploaded_files_directory / str(i),
            owner=CURRENT_USER,
            group=CURRENT_USER_GROUP,
            mode=0770))
    return [], resources
