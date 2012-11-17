from __future__ import unicode_literals, print_function, division
import logging
from veil.utility.hash import *
from veil.utility.path import *
from veil.model.collection import *
from veil.environment.setting import *

LOGGER = logging.getLogger(__name__)
instances = {} # purpose => instance

def register_bucket(purpose):
    return lambda: require_bucket(purpose)


def get_bucket_options(purpose):
    config = get_settings()['{}_bucket'.format(purpose)]
    return objectify({
        'type': config.type,
        'base_directory': config.base_directory,
        'base_url': config.base_url
    })


def require_bucket(purpose):
    if purpose not in instances:
        bucket_options = get_bucket_options(purpose)
        bucket_type = bucket_options.type
        if 'filesystem' == bucket_type:
            instances[purpose] = FilesystemBucket(
                bucket_options.base_directory, bucket_options.base_url)
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
        path = self.to_path(key)
        path.parent.makedirs(mode=0770)
        with path.open('wb') as f:
            for chunk in iter_file_in_chunks(file):
                f.write(chunk)

    def retrieve(self, key):
        return open(self.to_path(key), 'rb')

    def get_url(self, key):
        if key:
            path = self.to_path(key)
            if path.exists():
                with open(path) as f:
                    hash = calculate_file_md5_hash(f)
                return '{}/{}?v={}'.format(self.base_url, key, hash)
            else:
                return '{}/{}'.format(self.base_url, key)
        else:
            return None

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