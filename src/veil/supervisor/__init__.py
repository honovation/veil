import veil.component

with veil.component.init_component(__name__):
    from .setting import supervisor_settings

    __all__ = [
        supervisor_settings.__name__
    ]