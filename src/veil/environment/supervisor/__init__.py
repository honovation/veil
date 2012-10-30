import veil.component

with veil.component.init_component(__name__):
    from .supervisor_setting import supervisor_settings
    from .supervisorctl import supervisorctl
    from .supervisorctl import is_supervisord_running

    __all__ = [
        supervisor_settings.__name__,
        supervisorctl.__name__,
        is_supervisord_running.__name__
    ]

    def init():
        from veil.environment.setting import register_settings_coordinator
        from .supervisor_setting import add_inet_http_server_to_nginx
        from .supervisor_setting import consolidate_program_groups

        register_settings_coordinator(add_inet_http_server_to_nginx)
        register_settings_coordinator(consolidate_program_groups)