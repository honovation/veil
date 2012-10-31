from __future__ import unicode_literals, print_function, division
import re
from veil.environment import *

RE_UPDATE = re.compile(r'UPDATE\s+(\w+)\s+', re.IGNORECASE)
RE_INSERT = re.compile(r'INSERT\s+(\w+)[\s\(]+', re.IGNORECASE)
RE_INSERT_INTO = re.compile(r'INSERT\s+INTO\s+(\w+)[\s\(]+', re.IGNORECASE)
RE_DELETE = re.compile(r'DELETE\s+FROM\s+(\w+)\s+', re.IGNORECASE)

def check_table_dependency(component_name, sql):
    if VEIL_SERVER not in {'development', 'test'}:
        return
    if not component_name:
        return
    check_writable_table_dependency(get_application_wrtitable_tables(), component_name, sql)


def check_writable_table_dependency(writable_tables, component_name, sql):
    writing_table_name = get_writing_table_name(sql)
    if writing_table_name and component_name not in writable_tables.get(writing_table_name, set()):
        raise Exception('{} should not write to table {}'.format(component_name, writing_table_name))


def get_writing_table_name(sql):
    match = RE_UPDATE.match(sql)
    if match:
        return match.group(1)
    match = RE_INSERT_INTO.match(sql)
    if match:
        return match.group(1)
    match = RE_INSERT.match(sql)
    if match:
        return match.group(1)
    match = RE_DELETE.match(sql)
    if match:
        return match.group(1)


