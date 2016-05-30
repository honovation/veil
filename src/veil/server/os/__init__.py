import veil_component

with veil_component.init_component(__name__):
    from .filesystem_installer import directory_resource
    from .filesystem_installer import file_resource
    from .filesystem_installer import symbolic_link_resource

    from .os_package_repository_installer import apt_repository_resource
    from .os_package_repository_installer import os_ppa_repository_resource

    from .os_package_installer import os_package_resource

    from .os_service_installer import os_service_auto_starting_resource

    from .java_installer import oracle_java_resource

    from .nodejs_installer import nodejs_apt_repository_resource

    __all__ = [
        directory_resource.__name__,
        file_resource.__name__,
        symbolic_link_resource.__name__,

        apt_repository_resource.__name__,
        os_ppa_repository_resource.__name__,

        os_package_resource.__name__,

        os_service_auto_starting_resource.__name__,

        oracle_java_resource.__name__,

        nodejs_apt_repository_resource.__name__,
    ]
