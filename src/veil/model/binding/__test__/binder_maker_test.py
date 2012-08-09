from __future__ import unicode_literals, print_function, division
import __builtin__
from veil.development.test import TestCase
from ..binder_maker import each
from ..field_binder import clamp_length, not_empty
from ..invalid import Invalid

class BinderMakerTest(TestCase):
    def setUp(self):
        super(BinderMakerTest, self).setUp()
        __builtin__.__dict__['_'] = lambda msg: msg

    def test_each_validator(self):
        with self.assertRaises(Invalid):
            each(not_empty, clamp_length(max=3))(['USD', 'RMB', 'Unknown'])