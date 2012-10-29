from __future__ import unicode_literals, print_function, division
import functools
import inspect
import traceback
from contextlib import contextmanager, closing
from functools import wraps
from logging import getLogger
import uuid
import veil.component
from veil.development.test import *
from veil.environment.setting import *

LOGGER = getLogger(__name__)

registry = {} # purpose => get_database_options
instances = {} # purpose => instance
adapter_classes = {} # database type => adapter class
dependencies = {}

def register_adapter_class(type, adapter_class):
    adapter_classes[type] = adapter_class


def register_database(purpose):
    dependencies.setdefault(veil.component.get_loading_component().__name__, set()).add(purpose)
    if purpose not in registry:
        registry[purpose] = register_database_options(purpose)
    return lambda: require_database(purpose)


def check_database_dependencies(component_names, expected_dependencies):
    component_name_prefix = ''.join(component_names)
    actual_dependencies = set()
    for component_name, component_dependencies in dependencies.items():
        if component_name.startswith(component_name_prefix):
            actual_dependencies = actual_dependencies.union(component_dependencies)
    unexpected_dependencies = actual_dependencies - set(expected_dependencies)
    if unexpected_dependencies:
        raise Exception('{} should not reference {}'.format(component_name_prefix, unexpected_dependencies))
    unreal_dependencies = set(expected_dependencies) - actual_dependencies
    if unreal_dependencies:
        raise Exception('{} did not reference {}'.format(component_name_prefix, unreal_dependencies))


def register_database_options(purpose):
    section = '{}_database'.format(purpose) # for example contact_index_database
    get_db_type = register_option(section, 'type')
    get_db_host = register_option(section, 'host')
    get_db_port = register_option(section, 'port', int)
    get_db_database = register_option(section, 'database')
    get_db_user = register_option(section, 'user')
    get_db_password = register_option(section, 'password')
    get_db_schema = register_option(section, 'schema', default='')

    def get_database_options():
        return {
            'type': get_db_type(),
            'host': get_db_host(),
            'port': get_db_port(),
            'database': get_db_database(),
            'user': get_db_user(),
            'password': get_db_password(),
            'schema': get_db_schema()
        }

    return get_database_options


def require_database(purpose):
    if purpose not in registry:
        raise Exception('database for purpose {} is not registered'.format(purpose))
    if purpose not in instances:
        get_database_options = registry[purpose]
        instances[purpose] = connect(purpose=purpose, **get_database_options())
    db = instances[purpose]
    executing_test = get_executing_test(optional=True)
    if executing_test:
        db.disable_autocommit()
        db.commit_transaction = lambda: None
        executing_test.addCleanup(db.rollback_transaction)
    return db


def close_databases():
    for database in instances.values():
        database.close()
    instances.clear()


def connect(purpose, type, host, port, database, user, password, schema):
    __import__('veil.backend.database.{}'.format(type))
    if type in adapter_classes:
        adapter = adapter_classes[type](
            host=host, port=port,
            database=database, user=user,
            password=password, schema=schema)
        db = Database(purpose, adapter)
        db.database = database
        return db
    else:
        raise Exception('unknown database type: {}'.format(type))


@contextmanager
def require_transaction_context(db):
    if db.autocommit is False:
        yield
    else:
        db.disable_autocommit()
        try:
            yield
        except:
            try:
                raise
            finally:
                db.rollback_transaction()
        else:
            db.commit_transaction()
        finally:
            db.enable_autocommit()


def transactional(database_provider):
    def wrap_with_transaction_context(method):
        @wraps(method)
        def wrapper(*args, **kwargs):
            with require_transaction_context(database_provider()):
                return method(*args, **kwargs)

        return wrapper

    return wrap_with_transaction_context


class Database(object):
    def __init__(self, purpose, conn):
        self.purpose = purpose
        self.opened_by = str('\n').join(traceback.format_stack())
        self.conn = conn

    @property
    def autocommit(self):
        return self.conn.autocommit

    @autocommit.setter
    def autocommit(self, on_off):
        self.conn.autocommit = on_off

    def disable_autocommit(self):
        if self.autocommit is not False:
            self.autocommit = False

    def enable_autocommit(self):
        if self.autocommit is not True:
            self.autocommit = True

    def rollback_transaction(self):
        try:
            self.conn.rollback_transaction()
        except:
            LOGGER.exception('Cannot rollback database transaction')

    def commit_transaction(self):
        try:
            self.conn.commit_transaction()
        except:
            LOGGER.exception('Cannot commit database transaction')
            raise

    def close(self):
        try:
            self.conn.close()
        except:
            LOGGER.exception('Cannot close database connection')

    def has_rows(self, sql, **kwargs):
        return self.get_scalar('SELECT EXISTS ({})'.format(sql), **kwargs)

    def execute(self, sql, **kwargs):
        return self._execute(sql, **kwargs)

    def executemany(self, sql, seq_of_parameters):
        return self._executemany(sql, seq_of_parameters)

    def list(self, sql, **kwargs):
        return self._query(sql, **kwargs)

    def list_scalar(self, sql, **kwargs):
        rows = self._query(sql, returns_dict_object=False, **kwargs)
        if rows and len(rows[0]) > 1:
            raise Exception('More than one columns returned with the sql {} {}'.format(sql, kwargs))
        return [row[0] for row in rows]

    def get(self, sql, **kwargs):
        rows = self._query(sql, **kwargs)
        if not rows:
            LOGGER.debug('No rows returned with the sql {} {}'.format(sql, kwargs))
            return None
        if len(rows) > 1:
            LOGGER.warning('More than one rows returned with the sql {} {}'.format(sql, kwargs))
        return rows[0]

    def get_scalar(self, sql, **kwargs):
        rows = self._query(sql, returns_dict_object=False, **kwargs)
        if not rows:
            LOGGER.debug('No rows returned with the sql {} {}'.format(sql, kwargs))
            return None
        if len(rows) > 1:
            LOGGER.warning('More than one rows returned with the sql {} {}'.format(sql, kwargs))
        if len(rows[0]) > 1:
            raise Exception('More than one columns returned with the sql {} {}'.format(sql, kwargs))
        return rows[0][0]

    def insert(self, table, objects=None, returns_id=False, should_insert=None, **value_providers):
        if objects is not None:
            if not objects:
                return None
        else:
            if not value_providers:
                return None

        column_names = list(value_providers.keys())

        def get_rows_values():
            if objects is not None:
                for column_name in column_names:
                    value_provider = value_providers[column_name]
                    if not inspect.isfunction(value_provider) and not isinstance(value_provider, functools.partial):
                        value_providers[column_name] = ConstValueProvider(value_provider)
                    else:
                        value_providers[column_name] = FunctionValueProvider(value_provider)
                for object in objects:
                    if should_insert and not should_insert(object):
                        continue
                    yield [value_providers[column_name](object) for column_name in column_names]
            else:
                yield [value_providers[column_name] for column_name in column_names]

        fragments = ['INSERT INTO ', table, ' (']
        first = True
        arg_index = 0
        args = {}
        for column_name in column_names:
            if first:
                first = False
            else:
                fragments.append(', ')
            fragments.append(column_name)
        fragments.append(' ) VALUES ')
        first = True
        for row_values in get_rows_values():
            if first:
                first = False
            else:
                fragments.append(', ')
            first = True
            fragments.append('(')
            for cell_value in row_values:
                if first:
                    first = False
                else:
                    fragments.append(', ')
                arg_index += 1
                arg_name = ''.join(['a', unicode(arg_index)])
                fragments.append('%(')
                fragments.append(arg_name)
                fragments.append(')s')
                args[arg_name] = cell_value
            fragments.append(')')
        if returns_id:
            fragments.append(' RETURNING id')
            if objects:
                return self.list_scalar(''.join(fragments), **args)
            else:
                return self.get_scalar(''.join(fragments), **args)
        else:
            return self.execute(''.join(fragments), **args)

    def iter_in_batch(self, sql, batch_size=1, db_fetch_size=None, **kwargs):
        """
        batch_size: the number of rows to iterate at a time
        db_fetch_size: the number of rows to fetch from the db server at each network roundtrip
            during iteration on a named cursor
        """
        return self._query_large_result_set(sql, batch_size, db_fetch_size, **kwargs)

    def _execute(self, sql, **kwargs):
        with closing(self.conn.cursor(returns_dict_object=False)) as cursor:
            try:
                cursor.execute(sql, kwargs)
            except:
                LOGGER.error('failed to execute {} with {}'.format(sql, kwargs))
                raise
            return cursor.rowcount

    def _executemany(self, sql, seq_of_parameters):
        with closing(self.conn.cursor(returns_dict_object=False)) as cursor:
            try:
                cursor.executemany(sql, seq_of_parameters)
            except:
                LOGGER.error('failed to execute {} with {}'.format(sql, seq_of_parameters))
                raise
            return cursor.rowcount

    def _query(self, sql, returns_dict_object=True, **kwargs):
        with closing(self.conn.cursor(returns_dict_object=returns_dict_object)) as cursor:
            try:
                cursor.execute(sql, kwargs)
            except:
                LOGGER.error('failed to execute {} with {}'.format(sql, kwargs))
                raise
            return cursor.fetchall()

    def _query_large_result_set(self, sql, batch_size, db_fetch_size, returns_dict_object=True, **kwargs):
        """
        Run a query with potentially large result set using server-side cursor
        """
        # psycopg2 named cursor is implemented as 'DECLARE name CURSOR WITHOUT HOLD FOR query' and should be within a transaction and not be used in autocommit mode
        with require_transaction_context(self):
            cursor = self.conn.cursor(name=self._unique_cursor_name(), returns_dict_object=returns_dict_object)
            if db_fetch_size:
                cursor.itersize = db_fetch_size
            cursor.execute(sql, kwargs)
            rows = cursor.fetchmany(batch_size)
            while len(rows) > 0:
                yield rows
                rows = cursor.fetchmany(batch_size)
            cursor.close()
            # if exception happen before close, the whole transaction should be rolled back by the caller
            # if we close the cursor when sql execution error, the actuall error will be covered by unable to close cursor itself

    @staticmethod
    def _unique_cursor_name():
        return 'C{}'.format(uuid.uuid4().get_hex())


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __repr__(self):
        return 'Database {} opened by {}'.format(
            self.purpose, self.opened_by)


class FunctionValueProvider(object):
    def __init__(self, func):
        self.func = func
        self.multiple_args = len(inspect.getargspec(func).args) > 1

    def __call__(self, obj):
        if self.multiple_args:
            return self.func(*obj)
        else:
            return self.func(obj)


class ConstValueProvider(object):
    def __init__(self, const):
        self.const = const

    def __call__(self, obj):
        return self.const