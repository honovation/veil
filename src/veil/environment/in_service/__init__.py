import veil_component

with veil_component.init_component(__name__):
    from .container_installer import veil_env_containers_resource
    from .container_installer import veil_server_container_resource
    from .container_installer import veil_server_container_config_resource
    from .container_installer import veil_server_container_file_resource
    from .container_installer import veil_server_container_directory_resource
    from .server_installer import veil_env_servers_resource
    from .server_installer import veil_server_resource
    from .env_installer import get_deployed_at

    __all__ = [
        # from container_installer
        veil_env_containers_resource.__name__,
        veil_server_container_resource.__name__,
        veil_server_container_config_resource.__name__,
        veil_server_container_file_resource.__name__,
        veil_server_container_directory_resource.__name__,
        # from server_installer
        veil_env_servers_resource.__name__,
        veil_server_resource.__name__,
        # from env_installer
        get_deployed_at.__name__
    ]