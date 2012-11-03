from .installer import register_installer
from .python_package_installer import install_python_package
from .os_package_installer import install_os_package
from .component_installer import install_component

register_installer('python_package', install_python_package)
register_installer('os_package', install_os_package)
register_installer('component', install_component)
