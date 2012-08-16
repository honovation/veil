import sandal.component

with sandal.component.init_component(__name__):
    from .setting import supervisor_settings

    __all__ = [
        supervisor_settings.__name__
    ]