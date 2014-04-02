import veil_component

with veil_component.init_component(__name__):
    from .python_package_installer import get_python_package_installed_version
    from .python_package_installer import python_package_resource
    from .python_package_installer import python_sourcecode_package_resource
    from .veil_logging_level_config_installer import veil_logging_level_config_resource

    __all__ = [
        # from python_package_installer
        get_python_package_installed_version.__name__,
        python_package_resource.__name__,
        # from veil_log_config_installer
        veil_logging_level_config_resource.__name__,
        python_sourcecode_package_resource.__name__,
    ]
