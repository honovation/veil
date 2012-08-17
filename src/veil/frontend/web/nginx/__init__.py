import veil.component

with veil.component.init_component(__name__):
    from .setting import add_reverse_proxy_server
    from .setting import nginx_settings
    from .setting import nginx_program

    __all__ = [
        add_reverse_proxy_server.__name__,
        nginx_settings.__name__,
        nginx_program.__name__
    ]

    def init():
        from veil.environment.setting import register_settings_coordinator
        from .setting import copy_nginx_settings_to_veil

        register_settings_coordinator(copy_nginx_settings_to_veil)