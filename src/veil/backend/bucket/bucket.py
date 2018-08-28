# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import os
import re
import tempfile
from veil_component import as_path
from veil_installer import *
from veil.utility.misc import *
from .bucket_installer import bucket_config
from .bucket_installer import bucket_resource

LOGGER = logging.getLogger(__name__)

instances = {}  # purpose => instance


def register_bucket(purpose):
    add_application_sub_resource('{}_bucket'.format(purpose), lambda config: bucket_resource(purpose=purpose, config=config))
    return lambda: require_bucket(purpose)


def require_bucket(purpose):
    if purpose not in instances:
        config = bucket_config(purpose)
        bucket_type = config.type
        if 'filesystem' == bucket_type:
            instances[purpose] = FilesystemBucket(config.base_directory, config.base_url)
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

    def get_urls(self, key):
        raise NotImplementedError()

    @classmethod
    def validate_key(cls, key):
        raise NotImplementedError()


class FilesystemBucket(Bucket):
    BUCKET_KEY_PATTERN = re.compile(r'^[a-zA-Z0-9/._-]+$')

    def __init__(self, base_directory, base_url):
        super(FilesystemBucket, self).__init__()
        self.base_directory = as_path(base_directory)
        self.base_url = base_url

    def store(self, key, file_object):
        self.validate_key(key)
        path = self.to_path(key)
        path.parent.makedirs(mode=0770)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile('wb', suffix='---{}---tmp'.format(path.name), dir=path.parent, delete=False) as tf:
                temp_path = tf.name
                for chunk in iter_file_in_chunks(file_object):
                    tf.write(chunk)
            os.rename(temp_path, path)
        except:
            try:
                raise
            finally:
                if temp_path:
                    try:
                        os.remove(temp_path)
                    except Exception:
                        LOGGER.exception('exception while removing temp file: %(temp_path)s', {'temp_path': temp_path})

    def retrieve(self, key):
        return open(self.to_path(key), 'rb')

    def get_url(self, key):
        if not key:
            return ''
        path = self.to_path(key)
        if path.exists():
            with open(path) as f:
                hash = calculate_file_md5_hash(f)
            return '{}/{}?v={}'.format(self.base_url, key, hash)
        else:
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

    def get_urls(self, dir):
        assert dir is not None
        if not self.to_path(dir).exists():
            return []
        return [self.get_url(os.path.join(dir, f)) for f in os.listdir(self.to_path(dir)) if os.path.isfile(self.base_directory.joinpath(os.path.join(dir, f)))]

    @classmethod
    def validate_key(cls, key):
        if cls.BUCKET_KEY_PATTERN.match(key) is None:
            raise InvalidBucketKey('非法的Bucket key：由英文字母、数字、下划线、减号构成，不能有空格')


class InvalidBucketKey(Exception):
    pass
