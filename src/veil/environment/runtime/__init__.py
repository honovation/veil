import sandal.component

with sandal.component.init_component(__name__):
    from .option import register_option
    from .option import update_options
    from .bootstrapper import bootstrap_runtime

    __all__ = [
        # from option
        register_option.__name__,
        update_options.__name__,
        # from bootstrapper
        bootstrap_runtime.__name__
    ]
