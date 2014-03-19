from __future__ import unicode_literals, print_function, division
import functools
import inspect
import traceback
from contextlib import contextmanager, closing
from functools import wraps
from logging import getLogger
import uuid
from veil.utility.encoding import to_unicode
from veil.env_const import VEIL_ENV_TYPE
from veil_component import *
from veil_installer import *
from veil.development.test import *
from veil.model.event import *
from veil.server.process import *
from .table_dependency import check_table_dependencies
from .database_client_installer import database_client_config
from .database_client_installer import database_client_resource

LOGGER = getLogger(__name__)

instances = {} # purpose => instance
adapter_classes = {} # database type => adapter class

def register_adapter_class(type, adapter_class):
    adapter_classes[type] = adapter_class


def register_database(purpose, verify_db=False):
    component_name = get_loading_component_name()
    if not can_use_database(component_name, purpose):
        raise Exception('{} can not use database {}'.format(component_name, purpose))
    add_application_sub_resource('{}_database_client'.format(purpose), lambda config: database_client_resource(purpose=purpose, config=config))
    return lambda: require_database(purpose, component_name, verify_db)


def can_use_database(component_name, purpose):
    for provider in list_dynamic_dependency_providers('database', purpose):
        authorized = component_name == provider or component_name.startswith('{}.'.format(provider))
        if authorized:
            return True
    return False


def require_database(purpose, component_name=None, verify_db=False):
    if get_loading_component_name():
        raise Exception('use register_database whenever possible')
    if verify_db and purpose in instances:
        instances[purpose].reconnect_if_broken_per_verification()
    if purpose not in instances:
        config = database_client_config(purpose).copy()
        __import__(config.pop('driver'))
        instances[purpose] = connect(purpose=purpose, **config)
    db = Database(purpose, component_name, instances[purpose])
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
    if type in adapter_classes:
        adapter = adapter_classes[type](host=host, port=port, database=database, user=user, password=password, schema=schema)
        return adapter
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
    def __init__(self, purpose, component_name, conn):
        self.purpose = purpose
        self.component_name = component_name
        self.opened_by = to_unicode(str('').join(traceback.format_stack()))
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
        if not seq_of_parameters:
            return 0
        return self._executemany(sql, seq_of_parameters)

    def list(self, sql, **kwargs):
        return self._query(sql, **kwargs)

    def list_scalar(self, sql, **kwargs):
        rows = self._query(sql, returns_dict_object=False, **kwargs)
        if rows and len(rows[0]) > 1:
            raise Exception('More than one columns returned: sql is %(sql)s and kwargs are %(kwargs)s', {
                'sql': sql,
                'kwargs': kwargs
            })
        return [row[0] for row in rows]

    def get(self, sql, **kwargs):
        rows = self._query(sql, **kwargs)
        if not rows:
            LOGGER.debug('No rows returned: sql is %(sql)s and kwargs are %(kwargs)s', {
                'sql': sql,
                'kwargs': kwargs
            })
            return None
        if len(rows) > 1:
            LOGGER.warning('More than one rows returned: sql is %(sql)s and kwargs are %(kwargs)s', {
                'sql': sql,
                'kwargs': kwargs
            })
        return rows[0]

    def get_scalar(self, sql, **kwargs):
        rows = self._query(sql, returns_dict_object=False, **kwargs)
        if not rows:
            LOGGER.debug('No rows returned: sql is %(sql)s and kwargs are %(kwargs)s', {
                'sql': sql,
                'kwargs': kwargs
            })
            return None
        if len(rows) > 1:
            LOGGER.warning('More than one rows returned: sql is %(sql)s and kwargs are %(kwargs)s', {
                'sql': sql,
                'kwargs': kwargs
            })
        if len(rows[0]) > 1:
            raise Exception('More than one columns returned: sql is %(sql)s and kwargs are %(kwargs)s', {
                'sql': sql,
                'kwargs': kwargs
            })
        return rows[0][0]

    def insert(self, table, objects=None, returns_id=False, returns_record=False, should_insert=None,
               **value_providers):
        if objects is not None:
            if not objects:
                return None if returns_id or returns_record else 0
        else:
            if not value_providers:
                return None if returns_id or returns_record else 0

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
        first_column_name = True
        arg_index = 0
        args = {}
        for column_name in column_names:
            if first_column_name:
                first_column_name = False
            else:
                fragments.append(', ')
            fragments.append(column_name)
        fragments.append(' ) VALUES ')
        first_row_values = True
        for row_values in get_rows_values():
            if first_row_values:
                first_row_values = False
            else:
                fragments.append(', ')
            first_column_value = True
            fragments.append('(')
            for column_value in row_values:
                if first_column_value:
                    first_column_value = False
                else:
                    fragments.append(', ')
                fragments.append('%(')
                arg_index += 1
                arg_name = ''.join(('a', unicode(arg_index)))
                fragments.append(arg_name)
                fragments.append(')s')
                args[arg_name] = column_value
            fragments.append(')')
        if returns_id:
            fragments.append(' RETURNING id')
            return self.list_scalar(''.join(fragments), **args) if objects else self.get_scalar(''.join(fragments), **args)
        elif returns_record:
            fragments.append(' RETURNING *')
            return self.list(''.join(fragments), **args) if objects else self.get(''.join(fragments), **args)
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
                check_table_dependencies(self.component_name, self.purpose, sql)
                cursor.execute(sql, kwargs)
            except Exception as e:
                LOGGER.exception('failed to execute statement: sql is %(sql)s and kwargs are %(kwargs)s', {
                    'sql': sql,
                    'kwargs': kwargs
                })
                self.conn.reconnect_if_broken_per_exception(e)
                raise
            else:
                return cursor.rowcount

    def _executemany(self, sql, seq_of_parameters):
        with closing(self.conn.cursor(returns_dict_object=False)) as cursor:
            try:
                check_table_dependencies(self.component_name, self.purpose, sql)
                cursor.executemany(sql, seq_of_parameters)
            except Exception as e:
                LOGGER.exception('failed to executemany statement: sql is %(sql)s and seq_of_parameters are %(seq_of_parameters)s', {
                    'sql': sql,
                    'seq_of_parameters': seq_of_parameters
                })
                self.conn.reconnect_if_broken_per_exception(e)
                raise
            else:
                return cursor.rowcount

    def _query(self, sql, returns_dict_object=True, **kwargs):
        with closing(self.conn.cursor(returns_dict_object=returns_dict_object)) as cursor:
            try:
                check_table_dependencies(self.component_name, self.purpose, sql)
                cursor.execute(sql, kwargs)
            except Exception as e:
                LOGGER.exception('failed to execute query: sql is %(sql)s and kwargs are %(kwargs)s', {
                    'sql': sql,
                    'kwargs': kwargs
                })
                self.conn.reconnect_if_broken_per_exception(e)
                raise
            else:
                return cursor.fetchall()

    def _query_large_result_set(self, sql, batch_size, db_fetch_size, returns_dict_object=True, **kwargs):
        """
        Run a query with potentially large result set using server-side cursor
        """
        try:
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
        except Exception as e:
            LOGGER.exception('failed to query large result set: sql is %(sql)s and kwargs are %(kwargs)s', {
                'sql': sql,
                'kwargs': kwargs
            })
            self.conn.reconnect_if_broken_per_exception(e)
            raise

    @staticmethod
    def _unique_cursor_name():
        return 'C{}'.format(uuid.uuid4().get_hex())


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __repr__(self):
        return 'Database {} opened by {}'.format(self.purpose, self.opened_by)


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


@event(EVENT_PROCESS_TEARDOWN)
def close_all_connections():
    for purpose, instance in instances.items():
        if 'test' != VEIL_ENV_TYPE:
            LOGGER.debug('close connection at exit: %(purpose)s', {'purpose': purpose})
        instance.close()