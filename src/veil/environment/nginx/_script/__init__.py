from __future__ import unicode_literals, print_function, division
import os
from sandal.script import *
from sandal.shell import *
from sandal.path import *
from sandal.template import *
from ...layout import init_env
from ...directory import create_directory
from ...file import create_file
from ...ubuntu import install_ubuntu_package, remove_service_auto_start

@script('install')
def install_nginx():
    options = init_env()
    install_ubuntu_package('nginx-extras')
    remove_service_auto_start('nginx', '/etc/rc0.d/K20nginx')
    create_directory(options.nginx.log_directory)
    create_file(options.nginx.config_file, get_template('nginx.conf.j2').render())
    DEFAULT_USER = os.getenv('SUDO_USER')
    assert DEFAULT_USER, 'must run script using sudo'
    DEFAULT_GROUP = DEFAULT_USER
    create_directory(options.nginx.inline_static_files_directory, owner=DEFAULT_USER, group=DEFAULT_GROUP, mode=0770)