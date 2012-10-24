import veil.component

with veil.component.init_component(__name__):
    from .supervisor_setting import supervisor_settings

    __all__ = [
        supervisor_settings.__name__
    ]

    def init():
        from veil.environment.setting import register_settings_coordinator
        from .supervisor_setting import add_supervisor_reverse_proxy_server

        register_settings_coordinator(add_supervisor_reverse_proxy_server)