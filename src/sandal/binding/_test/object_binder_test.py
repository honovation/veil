from __future__ import unicode_literals, print_function, division
import __builtin__
from unittest.case import TestCase
from sandal.binding.field_binder import not_empty, clamp_length
from sandal.binding.object_binder import *

class ObjectBinderTest(TestCase):
    def setUp(self):
        super(ObjectBinderTest, self).setUp()
        __builtin__.__dict__['_'] = lambda msg: msg

    def test_single_field_single_binder(self):
        binder = ObjectBinder({'name': not_empty, 'age': not_empty, })
        try:
            binder({'name': '', 'age': ''})
        except Invalid, e:
            pass
        self.assertEqual(2, len(e.fields_errors))

    def test_single_field_multiple_binders(self):
        binder = ObjectBinder({'name': (not_empty, clamp_length(min=3, max=5)) })
        try:
            binder({'name': 'a'})
        except Invalid, e:
            pass
        self.assertEqual(1, len(e.fields_errors))
