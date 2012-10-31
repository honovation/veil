from __future__ import unicode_literals, print_function, division
from veil.development.test import *
from .table_dependency import check_writable_table_dependency

class CheckWritableTableDependencyTest(TestCase):
    def test_select(self):
        check_writable_table_dependency({}, 'a', 'SELECT xxx FROM...')

    def test_unexpected_update(self):
        with self.assertRaises(Exception):
            check_writable_table_dependency({}, 'a', 'UPDATE xxx SET...')

    def test_expected_update(self):
        check_writable_table_dependency({'xxx': ['a']}, 'a', 'UPDATE xxx SET...')

    def test_unexpected_insert(self):
        with self.assertRaises(Exception):
            check_writable_table_dependency({}, 'a', 'INSERT xxx(col1, col2...')
        with self.assertRaises(Exception):
            check_writable_table_dependency({}, 'a', 'INSERT  xxx (col1, col2...')

    def test_unexpected_insert_into(self):
        with self.assertRaises(Exception):
            check_writable_table_dependency({}, 'a', 'INSERT INTO xxx(col1, col2...')
        with self.assertRaises(Exception):
            check_writable_table_dependency({}, 'a', 'INSERT INTO  xxx (col1, col2...')

    def test_expected_insert_into(self):
        check_writable_table_dependency({'xxx': ['a']}, 'a', 'INSERT INTO xxx(col1, col2...')

    def test_unexpected_delete_from(self):
        with self.assertRaises(Exception):
            check_writable_table_dependency({}, 'a', 'DELETE FROM xxx WHERE...')


