import sandal.component

with sandal.component.init_component(__name__):
    from .setting import register_settings_provider
    from .setting import get_settings
    from .setting import merge_settings
    from .setting import get_base_settings
    from .option import register_option
    from .option import update_options
    from .bootstrapper import bootstrap_runtime

    __all__ = [
        # from setting
        register_settings_provider.__name__,
        get_settings.__name__,
        merge_settings.__name__,
        get_base_settings.__name__,
        # from option
        register_option.__name__,
        update_options.__name__,
        # from bootstrapper
        bootstrap_runtime.__name__
    ]
