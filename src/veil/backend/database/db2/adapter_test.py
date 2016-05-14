from __future__ import unicode_literals, print_function, division
from unittest.case import TestCase
from .adapter import NamedParameterCursor


class NamedParameterCursorTest(TestCase):
    def test(self):
        cursor = NamedParameterCursor(self)
        cursor.execute('SELECT * FROM a WHERE b=%(c)s AND d=%(e)s', dict(c='c', e='e'))
        self.assertTrue(self.called)

    def execute(self, sql, args):
        self.called = True
        self.assertEqual('SELECT * FROM a WHERE b=? AND d=?', sql)
        self.assertEqual(('c', 'e'), args)