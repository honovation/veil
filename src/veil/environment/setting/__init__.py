import veil_component

with veil_component.init_component(__name__):
    from .setting import merge_settings
    from .setting import merge_multiple_settings
    from .setting import load_config_from

    __all__ = [
        merge_settings.__name__,
        merge_multiple_settings.__name__,
        load_config_from.__name__
    ]
