import veil_component

with veil_component.init_component(__name__):
    from .elk import elk_resource

    __all__ = [
        elk_resource.__name__,
    ]
