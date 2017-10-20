# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from unittest import TestCase
from .adapter import NamedParameterCursor


class NamedParameterCursorTest(TestCase):
    def setUp(self):

        class DummyCursor(object):
            pass

        self.np_cursor = NamedParameterCursor(DummyCursor())

    def test_translate_parameters_with_args(self):
        sql = 'SELECT * FROM t WHERE id=%(id)s'
        kwargs = dict(id=1)

        new_sql, params = self.np_cursor.translate_parameters(sql, kwargs)

        self.assertEqual(new_sql, 'SELECT * FROM t WHERE id=:id')
        self.assertEqual(params, dict(id=1))

    def test_translate_parameters_with_tuple(self):
        sql = 'SELECT * FROM t WHERE name IN %(names)s'
        kwargs = dict(names=tuple(['name1', 'name2']))

        new_sql, params = self.np_cursor.translate_parameters(sql, kwargs)

        self.assertEqual(new_sql, 'SELECT * FROM t WHERE name IN (:names0, :names1)')
        self.assertEqual(params, dict(names0='name1', names1='name2'))

    def test_translate_parameters_with_unicode(self):
        sql = 'SELECT * FROM t WHERE name IN %(names)s'
        kwargs = dict(names=tuple(['你好1', '你好2']))

        new_sql, params = self.np_cursor.translate_parameters(sql, kwargs)

        self.assertEqual(new_sql, 'SELECT * FROM t WHERE name IN (:names0, :names1)')
        self.assertEqual(params, dict(names0=b'\xe4\xbd\xa0\xe5\xa5\xbd1', names1=b'\xe4\xbd\xa0\xe5\xa5\xbd2'))
