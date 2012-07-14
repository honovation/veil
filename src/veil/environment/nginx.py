from sandal.script import *
from sandal.option import *
from sandal.shell import *
from sandal.path import *
from sandal.template import *
from .layout import VEIL_ETC_DIR, init_env
from .directory import create_directory
from .file import create_file

@script('install-nginx')
def install_nginx():
    init_env()
    options = peek_options()
    if not path('/usr/sbin/nginx').exists():
        shell_execute('apt-get install nginx-extras')
    if path('/etc/rc0.d/K20nginx').exists():
        shell_execute('update-rc.d -f nginx remove')
    create_directory(options['nginx']['log_directory'])
    create_file(VEIL_ETC_DIR / 'nginx.conf', get_template('nginx.conf.j2').render())