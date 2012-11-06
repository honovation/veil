from .installer import register_installer
from .installer import installer
from .filesystem_installer import directory_resource
from .filesystem_installer import install_file
from .filesystem_installer import file_resource
from .python_package_installer import is_python_package_installed
from .python_package_installer import install_python_package
from .python_package_installer import python_package_resource
from .component_installer import component_resource

__import__('veil_installer.os_package_installer')
__import__('veil_installer.filesystem_installer')
__import__('veil_installer.python_package_installer')
__import__('veil_installer.component_installer')