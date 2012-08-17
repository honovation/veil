from __future__ import unicode_literals, print_function, division
from cStringIO import StringIO
import tempfile
from veil.development.test import TestCase
from veil.utility.path import as_path
from veil.environment.setting import *
from .bucket import register_bucket

class FilesystemBucketTest(TestCase):
    def setUp(self):
        super(FilesystemBucketTest, self).setUp()
        self.temp_dir = as_path(tempfile.gettempdir())
        update_options({
            'test_bucket': {
                'type': 'filesystem',
                'base_directory': self.temp_dir
            }
        })

    def test_happy_path(self):
        bucket = register_bucket('test')
        bucket().store('a/b/c', StringIO('d'))
        self.assertEqual('d', bucket().retrieve('a/b/c').read())

    def test_hacking(self):
        bucket = register_bucket('test')
        with self.assertRaises(AssertionError):
            bucket().retrieve('/etc/sudoers').read()
        with self.assertRaises(AssertionError):
            bucket().retrieve('..').read()
