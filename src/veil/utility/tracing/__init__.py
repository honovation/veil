import veil_component
with veil_component.init_component(__name__):
    from .tracing import traced

    __all__ = [
        traced.__name__
    ]
