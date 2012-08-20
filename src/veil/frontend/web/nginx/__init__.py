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