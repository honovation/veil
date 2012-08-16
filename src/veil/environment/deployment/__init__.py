import sandal.component

with sandal.component.init_component(__name__):
    from .setting import register_deployment_settings_provider
    from .setting import get_deployment_settings
    from .setting import merge_settings
    from .setting import get_deployment_base_settings

    __all__ = [
        # from setting
        register_deployment_settings_provider.__name__,
        get_deployment_settings.__name__,
        merge_settings.__name__,
        get_deployment_base_settings.__name__
    ]
