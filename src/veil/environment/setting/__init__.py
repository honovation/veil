import veil.component

with veil.component.init_component(__name__):
    from .setting import add_settings
    from .setting import register_settings_coordinator
    from .setting import get_settings
    from .setting import merge_settings
    from .option import register_option
    from .option import update_options
    from .bootstrapper import bootstrap_runtime

    __all__ = [
        # from setting
        add_settings.__name__,
        register_settings_coordinator.__name__,
        get_settings.__name__,
        merge_settings.__name__,
        # from option
        register_option.__name__,
        update_options.__name__,
        # from bootstrapper
        bootstrap_runtime.__name__
    ]
