import veil_component

with veil_component.init_component(__name__):
    from .host_installer import veil_hosts_resource
    from .host_installer import veil_hosts_application_codebase_resource
    from .host_installer import veil_host_onetime_config_resource
    from .host_installer import veil_host_config_resource
    from .host_installer import veil_host_application_config_resource
    from .host_installer import veil_host_application_codebase_resource
    from .host_installer import veil_host_sources_list_resource
    from .host_installer import veil_host_init_resource
    from .host_installer import veil_lxc_config_resource
    from .host_installer import veil_host_directory_resource
    from .host_installer import veil_host_file_resource
    from .host_installer import veil_host_user_editor_resource
    from .container_installer import veil_container_resource
    from .container_installer import veil_container_lxc_resource
    from .container_installer import veil_container_onetime_config_resource
    from .container_installer import veil_container_config_resource
    from .container_installer import veil_container_sources_list_resource
    from .container_installer import veil_container_init_resource
    from .container_installer import veil_server_boot_script_resource
    from .container_installer import veil_container_file_resource
    from .container_installer import veil_container_directory_resource
    from .server_installer import veil_servers_resource
    from .server_installer import veil_server_resource
    from .env_installer import get_deployed_at

    __all__ = [
        # from host_installer
        veil_hosts_resource.__name__,
        veil_hosts_application_codebase_resource.__name__,
        veil_host_onetime_config_resource.__name__,
        veil_host_config_resource.__name__,
        veil_host_application_config_resource.__name__,
        veil_host_application_codebase_resource.__name__,
        veil_host_sources_list_resource.__name__,
        veil_host_init_resource.__name__,
        veil_lxc_config_resource.__name__,
        veil_host_directory_resource.__name__,
        veil_host_file_resource.__name__,
        veil_host_user_editor_resource.__name__,
        # from container_installer
        veil_container_resource.__name__,
        veil_container_lxc_resource.__name__,
        veil_container_onetime_config_resource.__name__,
        veil_container_config_resource.__name__,
        veil_container_sources_list_resource.__name__,
        veil_container_init_resource.__name__,
        veil_server_boot_script_resource.__name__,
        veil_container_file_resource.__name__,
        veil_container_directory_resource.__name__,
        # from server_installer
        veil_servers_resource.__name__,
        veil_server_resource.__name__,
        # from env_installer
        get_deployed_at.__name__
    ]