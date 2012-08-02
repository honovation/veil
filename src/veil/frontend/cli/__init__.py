import sandal.component

with sandal.component.init_component(__name__):
    from .script import script
    from .script import execute_script

    __all__ = [
        # from script
        script.__name__,
        execute_script.__name__
    ]
