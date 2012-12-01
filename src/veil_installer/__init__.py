import veil_component

with veil_component.init_component(__name__):
    from .installer import atomic_installer
    from .installer import composite_installer
    from .installer import get_dry_run_result
    from .installer import do_install
    from .installer import application_resource
    from .installer import add_application_sub_resource
    from .installer import get_executing_composite_installer
    from .filesystem_installer import directory_resource
    from .filesystem_installer import file_resource
    from .filesystem_installer import symbolic_link_resource
    from .component_installer import component_resource
    from .component_installer import installer_resource
    from .os_package_installer import os_package_resource
    from .os_package_installer import is_os_package_installed
    from .os_service_installer import os_service_resource
    from .downloaded_file_installer import downloaded_file_resource
    from .shell import shell_execute
    from .shell import ShellExecutionError

    __all__ = [
        # from installer
        atomic_installer.__name__,
        composite_installer.__name__,
        get_dry_run_result.__name__,
        do_install.__name__,
        application_resource.__name__,
        add_application_sub_resource.__name__,
        get_executing_composite_installer.__name__,
        # from filesystem_installer
        directory_resource.__name__,
        file_resource.__name__,
        symbolic_link_resource.__name__,
        # from component_installer
        component_resource.__name__,
        installer_resource.__name__,
        # from os_package_installer
        os_package_resource.__name__,
        is_os_package_installed.__name__,
        # from os_service_installer
        os_service_resource.__name__,
        # from shell
        shell_execute.__name__,
        ShellExecutionError.__name__
    ]
