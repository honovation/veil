from __future__ import unicode_literals, print_function, division
from cStringIO import StringIO
import tempfile
from veil_component import VEIL_ENV
from veil_component import as_path
from veil.development.test import *
from .bucket import register_bucket
from .bucket_installer import override_bucket_config

if VEIL_ENV.is_test:
    bucket = register_bucket('test')


class FilesystemBucketTest(TestCase):
    def setUp(self):
        super(FilesystemBucketTest, self).setUp()
        self.temp_dir = as_path(tempfile.gettempdir())
        override_bucket_config('test', type='filesystem', base_directory=self.temp_dir, base_url=None)

    def test_happy_path(self):
        bucket().store('a/b/c', StringIO('d'))
        self.assertEqual('d', bucket().retrieve('a/b/c').read())
        bucket().store('a/b/c', StringIO('dd'))
        self.assertEqual('dd', bucket().retrieve('a/b/c').read())

    def test_hacking(self):
        with self.assertRaises(AssertionError):
            bucket().retrieve('/etc/sudoers').read()
        with self.assertRaises(AssertionError):
            bucket().retrieve('..').read()
