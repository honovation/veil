######## export begin
from ..layout import VEIL_HOME
from .nginx import NGINX_BASE_SETTINGS
from .nginx import create_nginx_server_settings
from .setting import register_environment_settings_provider
from .setting import get_environment_settings
from .ubuntu_package import install_ubuntu_package
from .ubuntu_package import remove_service_auto_start
from .python_package import install_python_package
from .filesystem import create_file
from .filesystem import delete_file
from .filesystem import create_symbolic_link

VEIL_HOME = VEIL_HOME
NGINX_BASE_SETTINGS = NGINX_BASE_SETTINGS

__all__ = [
    # from layout
    'VEIL_HOME',
    # from nginx
    'NGINX_BASE_SETTINGS',
    create_nginx_server_settings.__name__,
    # from setting
    register_environment_settings_provider.__name__,
    get_environment_settings.__name__,
    # from ubuntu_package
    install_ubuntu_package.__name__,
    remove_service_auto_start.__name__,
    # from python_package
    install_python_package.__name__,
    # from filesystem
    create_file.__name__,
    delete_file.__name__,
    create_symbolic_link.__name__
]
######## export end

def init():
    from sandal.component import init_component

    init_component(__name__)

init()