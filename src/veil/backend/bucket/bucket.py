from __future__ import unicode_literals, print_function, division
import logging
from veil.utility.path import as_path
from veil.environment.setting import *

LOGGER = logging.getLogger(__name__)
registry = {} # purpose => get_bucket_options
instances = {} # purpose => instance

def register_bucket(purpose, optional=False):
    if purpose not in registry:
        registry[purpose] = register_bucket_options(purpose, optional)
    return lambda: require_bucket(purpose)


def register_bucket_options(purpose, optional):
    get_type = register_option(
        '{}_bucket'.format(purpose), 'type', default='' if optional else None)
    get_base_directory = register_option(
        '{}_bucket'.format(purpose), 'base_directory', default='' if optional else None)
    get_base_url = register_option(
        '{}_bucket'.format(purpose), 'base_url', default='' if optional else None)

    def get_bucket_options():
        return {
            'type': get_type(),
            'base_directory': get_base_directory(),
            'base_url': get_base_url()
        }

    return get_bucket_options


def require_bucket(purpose):
    if purpose not in registry:
        raise Exception('bucket for purpose {} is not registered'.format(purpose))
    if purpose not in instances:
        bucket_options = registry[purpose]()
        bucket_type = bucket_options['type']
        if 'filesystem' == bucket_type:
            instances[purpose] = FilesystemBucket(
                bucket_options['base_directory'], bucket_options['base_url'])
        else:
            raise NotImplementedError('unknown bucket type: {}'.format(bucket_type))
    return instances[purpose]


class Bucket(object):
    def store(self, key, file):
        raise NotImplementedError()

    def retrieve(self, key):
        raise NotImplementedError()

    def get_url(self, key):
        raise NotImplementedError()

    def delete(self, key):
        raise NotImplementedError()

    def is_existing(self, key):
        raise NotImplementedError()


class FilesystemBucket(Bucket):
    def __init__(self, base_directory, base_url):
        super(FilesystemBucket, self).__init__()
        self.base_directory = as_path(base_directory)
        self.base_url = base_url

    def store(self, key, file):
        path = self.base_directory.joinpath(key)
        directory = path.parent
        assert directory.abspath().startswith(self.base_directory.abspath())
        directory.makedirs(mode=0770)
        with path.open('wb') as f:
            for chunk in iter_file_in_chunks(file):
                f.write(chunk)

    def retrieve(self, key):
        return open(self.to_path(key), 'rb')

    def get_url(self, key):
        return '{}/{}'.format(self.base_url, key)

    def delete(self, key):
        self.to_path(key).remove()

    def is_existing(self, key):
        return self.to_path(key).exists()

    def to_path(self, key):
        assert key is not None
        path = self.base_directory.joinpath(key)
        assert path.abspath().startswith(self.base_directory.abspath())
        return path


def iter_file_in_chunks(file_object, chunk_size=8192):
    """Lazy function (generator) to read a file piece by piece.
    Default chunk size: 8k."""
    return iter(lambda: file_object.read(chunk_size), b'')