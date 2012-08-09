import sandal.component

with sandal.component.init_component(__name__):
    from .bucket import register_bucket

    __all__ = [
        # from bucket
        register_bucket.__name__
    ]