import veil_component

with veil_component.init_component(__name__):
    from .config_renderer import render_config

    __all__ = [
        render_config.__name__
    ]