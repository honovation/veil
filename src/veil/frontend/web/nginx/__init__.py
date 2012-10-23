import veil.component

with veil.component.init_component(__name__):
    from .nginx_setting import nginx_reverse_proxy_server_settings
    from .nginx_setting import nginx_reverse_proxy_static_file_location_settings
    from .nginx_setting import nginx_settings

    __all__ = [
        nginx_reverse_proxy_server_settings.__name__,
        nginx_reverse_proxy_static_file_location_settings.__name__,
        nginx_settings.__name__
    ]