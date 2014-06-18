import veil_component

with veil_component.init_component(__name__):
    from .bucket import register_bucket
    from .bucket import FilesystemBucket
    from .bucket import InvalidBucketKey
    from .bucket_installer import bucket_resource

    __all__ = [
        register_bucket.__name__,
        FilesystemBucket.__name__,
        InvalidBucketKey.__name__,
        bucket_resource.__name__
    ]