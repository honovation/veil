# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import __builtin__
from veil.development.test import TestCase
from veil.model.binding import *
from .command import command
from .command import InvalidCommand


class StrictCommandHandlerTest(TestCase):
    def setUp(self):
        super(StrictCommandHandlerTest, self).setUp()
        __builtin__.__dict__['_'] = lambda msg: msg

    def test_command_binder_involved(self):
        strict_handler('a', 'b')
        with self.assertRaises(InvalidCommand):
            strict_handler('', 'b')
        with self.assertRaises(InvalidCommand):
            strict_handler(None, 'b')

    def test_pass_extra_positional_arguments(self):
        with self.assertRaises(Exception):
            strict_handler('a', 'b', 'c')

    def test_pass_extra_keyword_arguments(self):
        with self.assertRaises(Exception):
            strict_handler('a', 'b', extra='c')

    def test_pass_too_few_arguments(self):
        with self.assertRaises(InvalidCommand):
            strict_handler('a')


@command
def strict_handler(field1=not_empty, field2=not_empty):
    return field1, field2


class LooseCommandHandlerTest(TestCase):
    def setUp(self):
        super(LooseCommandHandlerTest, self).setUp()
        __builtin__.__dict__['_'] = lambda msg: msg

    def test_pass_extra_positional_arguments(self):
        field1, field2, args, kwargs = loose_handler('a', 'b', 'c')
        self.assertEqual('a', field1)
        self.assertEqual('b', field2)
        self.assertEqual(('c',), args)
        self.assertEqual({}, kwargs)

    def test_pass_extra_keyword_arguments(self):
        field1, field2, args, kwargs = loose_handler('a', 'b', extra='c')
        self.assertEqual('a', field1)
        self.assertEqual('b', field2)
        self.assertEqual((), args)
        self.assertEqual({'extra': 'c'}, kwargs)

    def test_pass_too_few_arguments(self):
        field1, field2, args, kwargs = loose_handler('a')
        self.assertEqual('a', field1)
        self.assertIsNone(field2)
        self.assertEqual((), args)
        self.assertEqual({}, kwargs)


@command
def loose_handler(field1=not_empty, field2=anything, *args, **kwargs):
    return field1, field2, args, kwargs


class ComplexCommandHandlerTest(TestCase):
    def setUp(self):
        super(ComplexCommandHandlerTest, self).setUp()
        __builtin__.__dict__['_'] = lambda msg: msg

    def test_two_fields_one_binder_handler(self):
        two_fields_one_binder_handler(1, 1)
        with self.assertRaises(InvalidCommand):
            two_fields_one_binder_handler(1, 2)

    def test_one_field_two_binders_handler(self):
        self.assertEqual(0, one_field_two_binders_handler(None))
        self.assertEqual(1, one_field_two_binders_handler('1'))

    def test_complex_handler(self):
        complex_handler('10', '1', '1')
        with self.assertRaises(InvalidCommand):  # 单个field的值如果通过binder的验证，其值应该被保存下来用作组合验证时使用
            complex_handler('a', '1', '1')


def accept_one_and_one_only(values):
    if sum(values) == 2 and (1, 1) == values:
        return values
    raise Invalid('I do not like them')


@command({('field1', 'field2'): accept_one_and_one_only})
def two_fields_one_binder_handler(field1=anything, field2=anything):
    return field1, field2


@command({('field2', 'field3'): accept_one_and_one_only})
def complex_handler(field1=to_integer, field2=(not_empty, to_integer), field3=(not_empty, to_integer)):
    return field1, field2, field3


@command
def one_field_two_binders_handler(field=(optional(to_integer), optional(default=0))):
    return field


class InvalidCommandHandlerTest(TestCase):
    def setUp(self):
        super(InvalidCommandHandlerTest, self).setUp()
        __builtin__.__dict__['_'] = lambda msg: msg

    def test_no_binder(self):
        with self.assertRaises(Exception):
            command(lambda a: None)
        with self.assertRaises(Exception):
            command(lambda a=None: None)
        with self.assertRaises(Exception):
            command(lambda a, b=not_empty: None)


class RaiseCommandErrorTest(TestCase):
    def test(self):
        with self.assertRaises(DummyException):
            raises_command_error_handler('abc')


@command
def raises_command_error_handler(dummy=not_empty):
    raise DummyException(dummy)


class DummyException(Exception):
    pass
