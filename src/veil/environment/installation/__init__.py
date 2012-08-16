import sandal.component

with sandal.component.init_component(__name__):
    from .installation import installation_script

    __all__ = [
        # from installation
        installation_script.__name__
    ]
