from __future__ import unicode_literals, print_function, division
import os
from veil.script import *
from sandal.template import *
from sandal.shell import *
from veil.environment import create_directory
from veil.environment import create_file
from veil.environment import remove_service_auto_start
from veil.environment import install_ubuntu_package
from veil.environment import get_environment_settings

@script('install')
def install_nginx():
    settings = get_environment_settings()
    install_ubuntu_package('nginx-extras')
    remove_service_auto_start('nginx', '/etc/rc0.d/K20nginx')
    create_directory(settings.nginx.log_directory)
    create_file(settings.nginx.config_file, get_template('nginx.conf.j2').render(config=settings.nginx))
    create_directory(
        settings.nginx.inline_static_files_directory,
        owner=settings.nginx.inline_static_files_owner,
        group=settings.nginx.inline_static_files_group,
        mode=0770)


@script('up')
def bring_up_nginx():
    settings = get_environment_settings()
    pass_control_to('nginx -c {}'.format(settings.nginx.config_file))
