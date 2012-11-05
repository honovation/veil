import veil_component

with veil_component.init_component(__name__):
    from .program_installer import program_installer

    __all__ = [
        program_installer.__name__
    ]
