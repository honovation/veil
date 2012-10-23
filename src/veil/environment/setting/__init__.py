import veil.component

with veil.component.init_component(__name__):
    from .setting import add_settings
    from .setting import register_settings_coordinator
    from .setting import get_settings
    from .setting import merge_settings
    from .setting import merge_multiple_settings
    from .setting import load_config_from
    from .option import register_option
    from .option import update_options
    from .bootstrapper import bootstrap_runtime
    from .bootstrapper import logging_settings

    __all__ = [
        # from setting
        add_settings.__name__,
        register_settings_coordinator.__name__,
        get_settings.__name__,
        merge_settings.__name__,
        merge_multiple_settings.__name__,
        load_config_from.__name__,
        # from option
        register_option.__name__,
        update_options.__name__,
        # from bootstrapper
        bootstrap_runtime.__name__,
        logging_settings.__name__
    ]
