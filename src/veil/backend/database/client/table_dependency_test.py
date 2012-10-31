from __future__ import unicode_literals, print_function, division
from veil.development.test import *
from .table_dependency import check_writable_table_dependencies
from .table_dependency import check_readable_table_dependencies

class CheckWritableTableDependencyTest(TestCase):
    def test_select(self):
        check_writable_table_dependencies({}, 'a', 'SELECT xxx FROM...')

    def test_unexpected_update(self):
        with self.assertRaises(Exception):
            check_writable_table_dependencies({}, 'a', 'UPDATE xxx SET...')

    def test_expected_update(self):
        check_writable_table_dependencies({'a': ['xxx']}, 'a', 'UPDATE xxx SET...')

    def test_unexpected_insert(self):
        with self.assertRaises(Exception):
            check_writable_table_dependencies({}, 'a', 'INSERT xxx(col1, col2...')
        with self.assertRaises(Exception):
            check_writable_table_dependencies({}, 'a', 'INSERT  xxx (col1, col2...')

    def test_unexpected_insert_into(self):
        with self.assertRaises(Exception):
            check_writable_table_dependencies({}, 'a', 'INSERT INTO xxx(col1, col2...')
        with self.assertRaises(Exception):
            check_writable_table_dependencies({}, 'a', 'INSERT INTO  xxx (col1, col2...')

    def test_expected_insert_into(self):
        check_writable_table_dependencies({'a': ['xxx']}, 'a', 'INSERT INTO xxx(col1, col2...')

    def test_unexpected_delete_from(self):
        with self.assertRaises(Exception):
            check_writable_table_dependencies({}, 'a', 'DELETE FROM xxx WHERE...')


class CheckReadableTableDependencyTest(TestCase):
    def test_expected_select(self):
        check_readable_table_dependencies({'a': ['xxx']}, 'a', 'SELECT * FROM xxx WHERE ...')

    def test_unexpected_select(self):
        with self.assertRaises(Exception):
            check_readable_table_dependencies({}, 'a', 'SELECT * FROM xxx WHERE ...')

    def test_multiple_from(self):
        check_readable_table_dependencies({'a': ['xxx', 'yyy']}, 'a', 'SELECT * FROM xxx, yyy WHERE ...')

    def test_multiple_from_with_as(self):
        check_readable_table_dependencies({'a': ['xxx', 'yyy']}, 'a', 'SELECT * FROM xxx AS x, yyy AS y WHERE ...')

    def test_left_join(self):
        check_readable_table_dependencies({'a': ['xxx', 'yyy']}, 'a', 'SELECT * FROM xxx LEFT JOIN yyy ON x=y WHERE ...')

    def test_unexpected_left_join(self):
        with self.assertRaises(Exception):
            check_readable_table_dependencies({'a': ['xxx']}, 'a', 'SELECT * FROM xxx LEFT JOIN yyy ON x=y WHERE ...')

    def test_unexpected_multiple_left_join(self):
        with self.assertRaises(Exception):
            check_readable_table_dependencies({'a': ['xxx', 'yyy']}, 'a',
                """
                SELECT * FROM xxx
                LEFT JOIN yyy ON x=y
                LEFT JOIN zzz ON x=z
                WHERE ...
                """)

    def test_right_join(self):
        check_readable_table_dependencies({'a': ['xxx', 'yyy']}, 'a',
            'SELECT * FROM xxx RIGHT OUTER JOIN yyy ON x=y WHERE ...')

    def test_inner_join(self):
        check_readable_table_dependencies({'a': ['xxx', 'yyy']}, 'a',
            'SELECT * FROM xxx INNER JOIN yyy ON x=y WHERE ...')

    def test_inner_join_then_left_join(self):
        check_readable_table_dependencies({'a': ['xxx', 'yyy', 'zzz']}, 'a',
            """
            SELECT * FROM xxx
            INNER JOIN yyy ON x=y
            LEFT JOIN zzz ON x=z
            WHERE ...
            """)

    def test_group_by(self):
        check_readable_table_dependencies({'a': ['xxx']}, 'a', 'SELECT * FROM xxx GROUP BY ...')

    def test_order_by(self):
        check_readable_table_dependencies({'a': ['xxx']}, 'a', 'SELECT * FROM xxx ORDER BY ...')

    def test_limit(self):
        check_readable_table_dependencies({'a': ['xxx']}, 'a', 'SELECT * FROM xxx LIMIT ...')

    def test_implicit_as(self):
        check_readable_table_dependencies({'a': ['xxx']}, 'a', 'SELECT * FROM xxx x WHERE ...')





