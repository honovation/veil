import veil_component

with veil_component.init_component(__name__):
    from .command import command
    from .command import InvalidCommand

    __all__ = [
        command.__name__,
        InvalidCommand.__name__,
    ]
