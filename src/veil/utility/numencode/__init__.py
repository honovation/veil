import veil_component

with veil_component.init_component(__name__):
    from .numencode import num2code
    from .numencode import code2num

    __all__ = [
        numencode.__name__,
        code2num.__name__
    ]
