import veil_component

with veil_component.init_component(__name__):
    from .filesystem_installer import directory_resource
    from .filesystem_installer import file_resource
    from .filesystem_installer import symbolic_link_resource
    from .os_package_repository_installer import os_ppa_repository_resource
    from .os_package_repository_installer import postgresql_apt_repository_resource
    from .os_package_repository_installer import elasticsearch_apt_repository_resource
    from .os_package_repository_installer import logstash_apt_repository_resource
    from .os_package_installer import os_package_resource
    from .os_service_installer import os_service_resource

    __all__ = [
        # from filesystem_installer
        directory_resource.__name__,
        file_resource.__name__,
        symbolic_link_resource.__name__,
        # from os_package_repository_installer
        os_ppa_repository_resource.__name__,
        postgresql_apt_repository_resource.__name__,
        elasticsearch_apt_repository_resource.__name__,
        logstash_apt_repository_resource.__name__,
        # from os_package_installer
        os_package_resource.__name__,
        # from os_service_installer
        os_service_resource.__name__,
    ]
