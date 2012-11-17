import veil_component

with veil_component.init_component(__name__):
    from .setting import register_settings_coordinator
    from .setting import initialize_settings
    from .setting import get_settings
    from .setting import merge_settings
    from .setting import merge_multiple_settings
    from .setting import load_config_from
    from .setting import override_test_settings

    __all__ = [
        # from setting
        register_settings_coordinator.__name__,
        initialize_settings.__name__,
        get_settings.__name__,
        merge_settings.__name__,
        merge_multiple_settings.__name__,
        load_config_from.__name__,
        override_test_settings.__name__,
    ]
