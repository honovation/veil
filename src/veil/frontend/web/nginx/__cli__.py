from __future__ import unicode_literals, print_function, division
from veil.utility.path import *
from veil.frontend.cli import *
from veil.frontend.template import *
from veil.backend.shell import *
from veil.environment.setting import *
from veil.environment.installation import *

@installation_script()
def install_nginx():
    settings = get_settings()
    install_ubuntu_package('nginx-extras')
    remove_service_auto_start('nginx', '/etc/rc0.d/K20nginx')
    create_directory(settings.nginx.log_directory)
    create_file(settings.nginx.config_file, get_template('nginx.conf.j2').render(config=settings.nginx))
    create_directory(
        settings.nginx.inline_static_files_directory,
        owner=settings.nginx.owner,
        group=settings.nginx.owner_group,
        mode=0770)
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


@script('up')
def bring_up_nginx():
    settings = get_settings()
    pass_control_to('nginx -c {}'.format(settings.nginx.config_file))
