import veil_component
with veil_component.init_component(__name__):
    from .host_installer import veil_hosts_resource
    from .host_installer import veil_hosts_codebase_resource
    from .host_installer import veil_host_onetime_config_resource
    from .host_installer import veil_host_config_resource
    from .host_installer import veil_host_application_config_resource
    from .host_installer import veil_host_codebase_resource
    from .host_installer import veil_host_sources_list_resource
    from .host_installer import veil_host_init_resource
    from .host_installer import veil_host_directory_resource
    from .host_installer import veil_host_file_resource
    from .host_installer import veil_host_iptables_rules_resource
    from .host_installer import veil_host_user_resource
    from .host_installer import veil_host_user_editor_additional_resource
    from .host_installer import veil_host_lxd_user_mapping_resource
    from .host_installer import veil_host_lxd_image_resource
    from .host_installer import veil_host_lxd_profile_resource
    from .container_installer import veil_container_resource
    from .container_installer import veil_container_lxc_resource
    from .container_installer import veil_container_onetime_config_resource
    from .container_installer import veil_container_config_resource
    from .container_installer import veil_container_init_resource
    from .container_installer import veil_server_boot_script_resource
    from .container_installer import veil_server_default_setting_resource
    from .container_installer import veil_container_file_resource
    from .container_installer import veil_container_sources_list_resource
    from .server_installer import veil_servers_resource
    from .server_installer import veil_server_resource
    from .server_installer import is_server_running
    from .env_installer import get_deployed_or_patched_at

    __all__ = [
        # from host_installer
        veil_hosts_resource.__name__,
        veil_hosts_codebase_resource.__name__,
        veil_host_onetime_config_resource.__name__,
        veil_host_config_resource.__name__,
        veil_host_application_config_resource.__name__,
        veil_host_codebase_resource.__name__,
        veil_host_sources_list_resource.__name__,
        veil_host_init_resource.__name__,
        veil_host_directory_resource.__name__,
        veil_host_file_resource.__name__,
        veil_host_iptables_rules_resource.__name__,
        veil_host_user_resource.__name__,
        veil_host_user_editor_additional_resource.__name__,
        veil_host_lxd_user_mapping_resource.__name__,
        veil_host_lxd_image_resource.__name__,
        veil_host_lxd_profile_resource.__name__,
        # from container_installer
        veil_container_resource.__name__,
        veil_container_lxc_resource.__name__,
        veil_container_onetime_config_resource.__name__,
        veil_container_config_resource.__name__,
        veil_container_init_resource.__name__,
        veil_server_boot_script_resource.__name__,
        veil_server_default_setting_resource.__name__,
        veil_container_file_resource.__name__,
        veil_container_sources_list_resource.__name__,
        # from server_installer
        veil_servers_resource.__name__,
        veil_server_resource.__name__,
        is_server_running.__name__,
        # from env_installer
        get_deployed_or_patched_at.__name__,
    ]