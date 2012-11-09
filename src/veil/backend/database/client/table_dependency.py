from __future__ import unicode_literals, print_function, division
import re
import veil_component
import logging
import traceback
from veil.environment import *
from veil.frontend.cli import *
from veil.frontend.encoding import *
from veil.development.architecture import check_architecture

RE_UPDATE = re.compile(r'UPDATE\s+(\w+)\s+', re.IGNORECASE)
RE_INSERT = re.compile(r'INSERT\s+(\w+)[\s\(]+', re.IGNORECASE)
RE_INSERT_INTO = re.compile(r'INSERT\s+INTO\s+(\w+)[\s\(]+', re.IGNORECASE)
RE_DELETE = re.compile(r'DELETE\s+FROM\s+(\w+)\s+', re.IGNORECASE)

# detect if it is select
RE_SELECT = re.compile(r'SELECT\s+', re.IGNORECASE)
# detect from begin
RE_FROM = re.compile(r'\s+FROM\s+', re.IGNORECASE)
# detect from end
RE_FROM_TERMINATORS = [
    re.compile(r'\s+WHERE\s+', re.IGNORECASE),
    re.compile(r'\s+(NATURAL\s+)?(INNER\s+)?JOIN\s+', re.IGNORECASE),
    re.compile(r'\s+(NATURAL\s+)?LEFT\s+(OUTER\s+)?JOIN\s+', re.IGNORECASE),
    re.compile(r'\s+(NATURAL\s+)?RIGHT\s+(OUTER\s+)?JOIN\s+', re.IGNORECASE),
    re.compile(r'\s+(NATURAL\s+)?FULL\s+(OUTER\s+)?JOIN\s+', re.IGNORECASE),
    re.compile(r'\s+(NATURAL\s+)?CROSS\s+JOIN\s+', re.IGNORECASE),
    re.compile(r'\s+GROUP\sBY\s+', re.IGNORECASE),
    re.compile(r'\s+ORDER\sBY\s+', re.IGNORECASE),
    re.compile(r'\s+LIMIT\s+', re.IGNORECASE)
]
# remove as
RE_AS = re.compile(r'\s+AS\s+\w+', re.IGNORECASE)
# pick tables from join
RE_JOIN = re.compile(r'\s+JOIN\s(\w+)\s+', re.IGNORECASE)

writable_tables = None # from __veil__.ARCHITECTURE
readable_tables = None # infer from writable_tables based on component dependencies
LOGGER = logging.getLogger(__name__)

def disable_logging():
    LOGGER.disabled = True


@script('writable-tables')
def print_writable_table_dependencies(threshold=8):
    print_table_dependencies_for(list_writable_tables(), threshold)


@script('readable-tables')
def print_readable_table_dependencies(threshold=8):
    print_table_dependencies_for(list_readable_tables(), threshold)


def print_table_dependencies_for(component_tables, threshold=8):
    threshold = int(threshold)
    for component_name in sorted(component_tables.keys()):
        tables = component_tables[component_name]
        if tables:
            tables = list(tables)
            if len(tables) > threshold:
                print('[{}]:\t{}...'.format(component_name, ', '.join(tables[:threshold])))
            else:
                print('[{}]:\t{}'.format(component_name, ', '.join(tables)))


def list_readable_tables():
    global readable_tables
    if readable_tables is not None:
        return readable_tables
    readable_tables = {}
    for component_name in veil_component.get_component_map().keys():
        readable_tables[component_name] = set(list_writable_tables().get(component_name, set()))
        transitive_dependencies = veil_component.get_transitive_dependencies(component_name)
        for dependency in transitive_dependencies:
            readable_tables[component_name] = readable_tables[component_name].union(
                set(list_writable_tables().get(dependency, set())))
    return readable_tables


def list_writable_tables():
    global writable_tables
    if writable_tables is not None:
        return writable_tables
    writable_tables = {}
    check_architecture() # which calls "update_writable_tables"
    return writable_tables


def update_writable_tables(component_names, expected_dependencies):
    if writable_tables is None:
        return
    writable_tables[''.join(component_names)] = expected_dependencies


def check_table_dependencies(component_name, sql):
    if VEIL_SERVER not in {'development', 'test'}:
        return
    if not component_name:
        return
    sql = to_unicode(sql)
    check_writable_table_dependencies(list_writable_tables(), component_name, sql)
    check_readable_table_dependencies(list_readable_tables(), component_name, sql)


def check_writable_table_dependencies(writable_tables, component_name, sql):
    sql = sql.strip().replace('\n', '').replace('\r', '').replace('\t', '')
    writing_table_name = get_writing_table_name(sql)
    if writing_table_name and writing_table_name not in writable_tables.get(component_name, set()):
        LOGGER.debug('readable tables: {}'.format(readable_tables))
        LOGGER.debug('writable tables: {}'.format(writable_tables))
        raise Exception('{} should not write to table {}'.format(
            component_name, writing_table_name))


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


def check_readable_table_dependencies(readable_tables, component_name, sql):
    sql = sql.strip().replace('\n', '').replace('\r', '').replace('\t', '')
    reading_table_names = get_reading_table_names(sql)
    component_tables = readable_tables.get(component_name, set())
    for table in reading_table_names:
        if table not in component_tables:
            LOGGER.debug('readable tables: {}'.format(readable_tables))
            LOGGER.debug('writable tables: {}'.format(writable_tables))
            raise Exception('{} should not read from table {}'.format(
                component_name, table))


def get_reading_table_names(sql):
    if not RE_SELECT.match(sql):
        return []
    match = RE_FROM.search(sql)
    if not match:
        return []
    sql = sql[match.end():] # remove stuff before FROM and FROM itself
    sql = RE_AS.sub('', sql) # remove AS xxx
    sql_froms, sql_joins = get_sql_froms_and_joins(sql)
    table_names = set(get_sql_froms_tables(sql_froms)).union(
        set(get_sql_joins_tables(sql_joins)))
    return [t.split(' ')[0] for t in table_names]


def get_sql_froms_and_joins(sql):
    positions = []
    for regex in RE_FROM_TERMINATORS:
        match = regex.search(sql)
        if match:
            positions.append(match.start())
    if positions:
        left_most_position = min(positions)
        return sql[:left_most_position], sql[left_most_position:]
    else:
        return sql, ''


def get_sql_froms_tables(sql_froms):
    return [table.strip() for table in sql_froms.split(',')]


def get_sql_joins_tables(sql_joins):
    return RE_JOIN.findall(sql_joins)
