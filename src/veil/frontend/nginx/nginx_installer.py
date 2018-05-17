from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *
from veil.frontend.nginx_setting import NGINX_PID_PATH


@composite_installer
def nginx_resource(servers, config):
    resources = [
        os_ppa_repository_resource(name='nginx/stable'),
        os_package_resource(name='nginx-extras'),
        os_service_auto_starting_resource(name='nginx', state='not_installed'),
        directory_resource(path=VEIL_LOG_DIR / 'nginx', owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        file_resource(path=VEIL_ETC_DIR / 'nginx.conf',
                      content=render_config('nginx.conf.j2',
                                            config=dict(config, owner=CURRENT_USER, owner_group=CURRENT_USER_GROUP,
                                                        log_directory=VEIL_LOG_DIR / 'nginx', pid_file=NGINX_PID_PATH,
                                                        servers=servers, DEFAULT_DNS_SERVERS=DEFAULT_DNS_SERVERS,
                                                        HTTP_STANDARD_PORT=80, HTTPS_STANDARD_PORT=443)), owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        file_resource(path=VEIL_ETC_DIR / 'nginx-https.cfg', content='\n'.join(
            '{}:{}'.format(server_name, ','.join(str(port) for port in server_properties['https_listens'])) for
            server_name, server_properties in servers.items() if server_properties['https_listens']), owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        directory_resource(path=VEIL_BUCKET_UPLOADED_FILES_DIR, owner=CURRENT_USER, group=CURRENT_USER_GROUP, mode=0770)
    ]
    resources.extend([
        directory_resource(path=VEIL_BUCKET_UPLOADED_FILES_DIR / unicode(i), owner=CURRENT_USER, group=CURRENT_USER_GROUP, mode=0770) for i in range(10)
    ])
    return resources
