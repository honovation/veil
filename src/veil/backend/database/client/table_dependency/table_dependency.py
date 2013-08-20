from __future__ import unicode_literals, print_function, division
import re
import veil_component
import logging
from veil.environment import *
from veil.frontend.cli import *
from veil.utility.encoding import *
from veil_component import *

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

SUB_QUERY_TOKEN = '__SUB_QUERY__'

writable_tables = None # from __veil__.ARCHITECTURE
readable_tables = None # infer from writable_tables based on component dependencies
LOGGER = logging.getLogger(__name__)

def disable_logging():
    LOGGER.disabled = True


@script('writable-tables')
def print_writable_table_dependencies(threshold=8):
    load_all_components()
    print_table_dependencies_for(list_writable_tables(), threshold)


@script('readable-tables')
def print_readable_table_dependencies(threshold=8):
    load_all_components()
    print_table_dependencies_for(list_readable_tables(), threshold)


def print_table_dependencies_for(component_tables, threshold=8):
    threshold = int(threshold)
    for component_name in sorted(component_tables.keys()):
        tables = component_tables[component_name]
        tables = ['{}/{}'.format(db, tbl) for db, tbl in tables]
        if tables:
            tables = list(tables)
            if len(tables) > threshold:
                LOGGER.info('[%(component_name)s]:\t%(tables)s...', {
                    'component_name': component_name,
                    'tables': ', '.join(tables[:threshold])
                })
            else:
                LOGGER.info('[%(component_name)s]:\t%(tables)s', {
                    'component_name': component_name,
                    'tables': ', '.join(tables)
                })


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
    providers, consumers = list_dynamic_dependencies()
    for component_name, deps in consumers.items():
        for dep in deps:
            dep_type, db_and_table = dep
            if 'table' != dep_type:
                continue
            purpose, table = db_and_table.split('/')
            readable_tables.setdefault(component_name, set()).add((purpose, table))
    return readable_tables


def list_writable_tables():
    global writable_tables
    if writable_tables is not None:
        return writable_tables
    writable_tables = {}
    providers, consumers = list_dynamic_dependencies()
    for dep, component_names in providers.items():
        dep_type, db_and_table = dep
        if 'table' != dep_type:
            continue
        purpose, table = db_and_table.split('/')
        for component_name in component_names:
            writable_tables.setdefault(component_name, set()).add((purpose, table))
    return writable_tables


def check_table_dependencies(component_name, purpose, sql):
    if VEIL_SERVER not in {'development', 'test'}:
        return
    if not component_name:
        return
    sql = to_unicode(sql)
    check_writable_table_dependencies(list_writable_tables(), component_name, purpose, sql)
    check_readable_table_dependencies(list_readable_tables(), component_name, purpose, sql)


def check_writable_table_dependencies(writable_tables, component_name, purpose, sql):
    sql = strip_sql(sql)
    writing_table_name = get_writing_table_name(sql)
    if writing_table_name and (purpose, writing_table_name) not in writable_tables.get(component_name, set()):
        raise Exception('{} should not write to table {} in database {}'.format(
            component_name, writing_table_name, purpose))


def get_writing_table_name(sql):
    sql = strip_sql(sql)
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


def strip_sql(sql):
    return ' '.join(sql.split())


def remove_parameter_labels(sql):
    return re.sub('%\(\w+\)s', '', sql)


def remove_insert_values(sql):
    return re.sub('values\s?\(.*?\)(\s?,\s?\(.*?\))*', '', sql, flags=re.I)


def check_readable_table_dependencies(readable_tables, component_name, purpose, sql):
    sql = strip_sql(sql)
    sql = remove_parameter_labels(sql)
    sql = remove_insert_values(sql)
    reading_table_names = set()
    sub_queries = []
    extract_sub_queries(sql, sub_queries)
    for sub_query in sub_queries:
        reading_table_names = reading_table_names.union(get_reading_table_names(sub_query))
    reading_table_names -= {SUB_QUERY_TOKEN}
    component_tables = readable_tables.get(component_name, set())
    for table in reading_table_names:
        if (purpose, table) not in component_tables:
            raise Exception('{} should not read from table {} in database {}'.format(
                component_name, table, purpose))


def extract_sub_queries(sql, queries):
    if not sql:
        return
    left = sql.find('(')
    if left == -1:
        queries.append(sql)
        return
    right = sql.find(')', left + 1)
    if right == -1:
        queries.append(sql)
        return
    inner_left = sql.find('(', left + 1, right)
    if inner_left == -1:
        queries.append(sql[left+1:right])
        extract_sub_queries('{} {} {}'.format(sql[:left], SUB_QUERY_TOKEN, sql[right+1:]), queries)
        return
    pos = left
    count = 1
    while count > 0:
        pos += 1
        if sql[pos] == '(':
            count += 1
        elif sql[pos] == ')':
            count -= 1
        else:
            pass
    extract_sub_queries(sql[left+1:pos], queries)
    extract_sub_queries('{} {} {}'.format(sql[:left], SUB_QUERY_TOKEN, sql[pos+1:]), queries)
    return


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
    return [t.split(' ')[0] for t in table_names if t and t[0] != '(']


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
