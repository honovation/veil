import veil.component

with veil.component.init_component(__name__):
    from .bucket import register_bucket
    from .bucket_setting import bucket_settings

    __all__ = [
        register_bucket.__name__,
        bucket_settings.__name__
    ]

    def init():
        from veil.environment.setting import register_settings_coordinator
        from .bucket_setting import add_bucket_reverse_proxy_static_file_locations

        register_settings_coordinator(add_bucket_reverse_proxy_static_file_locations)