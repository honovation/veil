from __future__ import unicode_literals, print_function, division
from cStringIO import StringIO
import tempfile
from veil.development.test import TestCase
from veil.utility.path import as_path
from .bucket import register_bucket
from .bucket_installer import override_bucket_config

bucket = register_bucket('test')

class FilesystemBucketTest(TestCase):
    def setUp(self):
        super(FilesystemBucketTest, self).setUp()
        self.temp_dir = as_path(tempfile.gettempdir())
        override_bucket_config('test', type='filesystem', base_directory=self.temp_dir, base_url=None)

    def test_happy_path(self):
        bucket().store('a/b/c', StringIO('d'))
        self.assertEqual('d', bucket().retrieve('a/b/c').read())

    def test_hacking(self):
        with self.assertRaises(AssertionError):
            bucket().retrieve('/etc/sudoers').read()
        with self.assertRaises(AssertionError):
            bucket().retrieve('..').read()
