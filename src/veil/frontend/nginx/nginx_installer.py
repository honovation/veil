from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *
from veil.frontend.nginx_setting import NGINX_PID_PATH

@composite_installer
def nginx_resource(servers, config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        os_ppa_repository_resource(name='nginx/stable'),
        os_package_resource(name='nginx-extras'),
        os_service_resource(state='not_installed', name='nginx'),
        directory_resource(path=VEIL_LOG_DIR / 'nginx', owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        file_resource(path=VEIL_ETC_DIR / 'nginx.conf', content=render_config('nginx.conf.j2', config=dict({
            'owner': CURRENT_USER,
            'owner_group': CURRENT_USER_GROUP,
            'log_directory': VEIL_LOG_DIR / 'nginx',
            'pid_file': NGINX_PID_PATH,
            'servers': servers
        }, **config)))
    ])
    uploaded_files_directory = VEIL_BUCKETS_DIR / 'uploaded-files'
    resources.append(directory_resource(path=uploaded_files_directory, owner=CURRENT_USER, group=CURRENT_USER_GROUP, mode=0770))
    for i in range(10):
        resources.append(directory_resource(path=uploaded_files_directory / str(i), owner=CURRENT_USER, group=CURRENT_USER_GROUP, mode=0770))
    return resources
