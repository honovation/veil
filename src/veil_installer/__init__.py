import veil_component

with veil_component.init_component(__name__):
    from .installer import atomic_installer
    from .installer import composite_installer
    from .installer import get_dry_run_result
    from .installer import do_install
    from .installer import application_resource
    from .installer import add_application_sub_resource
    from .filesystem_installer import directory_resource
    from .filesystem_installer import file_resource
    from .filesystem_installer import symbolic_link_resource
    from .python_package_installer import is_python_package_installed
    from .python_package_installer import python_package_resource
    from .component_installer import component_resource
    from .os_package_installer import os_package_resource
    from .os_package_installer import is_os_package_installed
    from .os_service_installer import os_service_resource
    from .veil_log_config_installer import veil_log_config_resource
    from .shell import shell_execute
    from .shell import ShellExecutionError
    from .config_renderer import render_config

    __all__ = [
        # from installer
        atomic_installer.__name__,
        composite_installer.__name__,
        get_dry_run_result.__name__,
        do_install.__name__,
        application_resource.__name__,
        add_application_sub_resource.__name__,
        # from filesystem_installer
        directory_resource.__name__,
        file_resource.__name__,
        symbolic_link_resource.__name__,
        # from python_package_installer
        is_python_package_installed.__name__,
        python_package_resource.__name__,
        # from component_installer
        component_resource.__name__,
        # from os_package_installer
        os_package_resource.__name__,
        is_os_package_installed.__name__,
        # from os_service_installer
        os_service_resource.__name__,
        # from veil_log_config_installer
        veil_log_config_resource.__name__,
        # from shell
        shell_execute.__name__,
        ShellExecutionError.__name__,
        # from config_renderer
        render_config.__name__
    ]
