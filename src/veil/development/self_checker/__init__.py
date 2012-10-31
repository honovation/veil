import veil_component

with veil_component.init_component(__name__):
    from .checker import register_self_checker

    __all__ = [
        register_self_checker.__name__
    ]