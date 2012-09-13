from __future__ import unicode_literals, print_function, division
from veil.utility.path import *
from veil.frontend.template import *
from veil.environment import *
from veil.environment.setting import *
from veil.environment.installation import *

@installation_script()
def install_nginx():
    settings = get_settings()
    if not getattr(settings, 'nginx', None):
        return
    install_ubuntu_package('nginx-extras')
    remove_service_auto_start('nginx', '/etc/rc0.d/K20nginx')
    create_directory(settings.nginx.log_directory, owner=CURRENT_USER, group=CURRENT_USER_GROUP)
    create_file(settings.nginx.config_file, get_template('nginx.conf.j2').render(config=settings.nginx))
    uploaded_files_directory = as_path(settings.nginx.uploaded_files_directory)
    create_directory(
        uploaded_files_directory,
        owner=settings.nginx.owner,
        group=settings.nginx.owner_group,
        mode=0770)
    for i in range(10):
        create_directory(
            uploaded_files_directory / str(i),
            owner=settings.nginx.owner,
            group=settings.nginx.owner_group,
            mode=0770)
