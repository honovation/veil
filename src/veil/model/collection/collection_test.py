from __future__ import unicode_literals, print_function, division
from unittest.case import TestCase
from .collection import single_or_none
from .collection import first_or_none
from .collection import single
from .collection import DictObject


class SingleOrNoneTest(TestCase):
    def test(self):
        self.assertIsNone(single_or_none([]))
        self.assertEqual(1, single_or_none([1]))
        self.assertRaises(Exception, lambda : single_or_none([1, 2]))


class SingleTest(TestCase):
    def test(self):
        self.assertRaises(Exception, lambda : single([]))
        self.assertEqual(1, single([1]))
        self.assertRaises(Exception, lambda : single([1, 2]))


class FirstOrNoneTest(TestCase):
    def test(self):
        self.assertIsNone(first_or_none([]))
        self.assertEqual(1, first_or_none([1]))
        self.assertEqual(1, first_or_none([1, 2]))


class DictObjectTest(TestCase):
    def test_get_set(self):
        o = DictObject()
        o['hello'] = 'world'
        self.assertEqual('world', o.hello)
        o.world = 'hello'
        self.assertEqual('hello', o['world'])

    def test_in(self):
        o = DictObject()
        o['hello'] = 'world'
        self.assertIn('hello', o)
        self.assertNotIn('world', o)

    def test_hasattr(self):
        self.assertFalse(hasattr(DictObject(), 'hello'))
        self.assertTrue(hasattr(DictObject(hello='world'), 'hello'))

    def test_get_not_existing_attribute(self):
        with self.assertRaises(AttributeError):
            DictObject().hello
