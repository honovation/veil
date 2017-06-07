from __future__ import unicode_literals, print_function, division
import functools
import inspect
import traceback
from contextlib import contextmanager, closing
from functools import wraps
from logging import getLogger
import uuid
from veil.model.collection import *
from veil_component import *
from veil_installer import *
from veil.utility.encoding import *
from veil.development.test import *
from veil.model.event import *
from veil.server.process import *
from .table_dependency import check_table_dependencies
from .database_client_installer import database_client_config
from .database_client_installer import database_client_resource

LOGGER = getLogger(__name__)

DATABASE_TYPE_POSTGRESQL = 'postgresql'
DATABASE_TYPE_ORACLE = 'oracle'
DATABASE_TYPE_DB2 = 'db2'
DATABASE_TYPE_MSSQL = 'mssql'
DATABASE_TYPE_MYSQL = 'mysql'

instances = {}  # purpose => adapter instance
adapter_classes = {}  # database type => adapter class


def register_adapter_class(type_, adapter_class):
    adapter_classes[type_] = adapter_class


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
        config['type_'] = config.pop('type')
        __import__(config.pop('driver'))
        instances[purpose] = connect(**config)
        assert instances[purpose].autocommit, 'autocommit should be enabled by default'
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


def connect(type_, host, port, database, user, password, schema=None, **ignore):
    if type_ not in adapter_classes:
        raise Exception('unknown database type: {}'.format(type_))
    adapter = adapter_classes[type_](host=host, port=port, database=database, user=user, password=password, schema=schema)
    return adapter


@contextmanager
def require_transaction_context(db):
    if db.autocommit:
        db.disable_autocommit()
        try:
            yield
        except:
            try:
                raise
            finally:
                try:
                    db.rollback_transaction()
                except Exception:
                    pass
        else:
            db.commit_transaction()
        finally:
            db.enable_autocommit()
    else:
        yield


def transactional(database_provider):
    def wrap_with_transaction_context(method):
        @wraps(method)
        def wrapper(*args, **kwargs):
            db = database_provider()
            if db.autocommit:
                while True:
                    try:
                        with require_transaction_context(db):
                            return method(*args, **kwargs)
                    except ReconnectedWithinTransactionException:
                        continue
            else:
                return method(*args, **kwargs)
        return wrapper

    return wrap_with_transaction_context


class Database(object):
    def __init__(self, purpose, component_name, conn):
        self.purpose = purpose
        self.component_name = component_name
        self.opened_by = to_unicode(b''.join(traceback.format_stack()), strict=False)
        self.conn = conn

    @property
    def autocommit(self):
        return self.conn.autocommit

    @autocommit.setter
    def autocommit(self, on_off):
        reconnected = False
        while True:
            try:
                self.conn.autocommit = on_off
            except Exception as e:
                if reconnected:
                    LOGGER.exception('failed to set autocommit: %(on_off)s', {'on_off': on_off})
                    raise
                reconnected = self.conn.reconnect_if_broken_per_exception(e)
                if not reconnected:
                    LOGGER.exception('failed to set autocommit: %(on_off)s', {'on_off': on_off})
                    raise
            else:
                break

    def disable_autocommit(self):
        if self.autocommit:
            self.autocommit = False

    def enable_autocommit(self):
        if not self.autocommit:
            self.autocommit = True

    def rollback_transaction(self):
        try:
            self.conn.rollback_transaction()
        except Exception:
            LOGGER.exception('Cannot rollback database transaction')
            raise

    def commit_transaction(self):
        try:
            self.conn.commit_transaction()
        except Exception:
            LOGGER.exception('Cannot commit database transaction')
            raise

    def close(self):
        try:
            self.conn.close()
        except Exception:
            LOGGER.exception('Cannot close database connection')

    def exists(self, sql, **kwargs):
        if self.conn.type == DATABASE_TYPE_ORACLE:
            return self.get_scalar('SELECT 1 FROM DUAL WHERE EXISTS ({})'.format(sql), **kwargs) is not None
        return self.get_scalar('SELECT EXISTS ({})'.format(sql), **kwargs)

    def execute(self, sql, **kwargs):
        return self._execute(sql, **kwargs)

    def executemany(self, sql, seq_of_parameters, should_insert=None):
        if should_insert:
            seq_of_parameters = [e for e in seq_of_parameters if should_insert(e)]
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

    def insert(self, table, objects=None, returns_id=False, returns_record=False, returns_entity=False, should_insert=None, include_attributes=None,
               exclude_columns=(), conflict_target='', conflict_action='', **value_providers):
        """
        include_attributes:
            when it is None, add all attributes not in exclude_columns to columns;
            when it is empty tuple, do not add attributes to columns;
            when it is not None and not empty tuple, add include_attributes not in exclude_columns to columns;
        """
        value_providers.pop('_key_', None)
        if exclude_columns:
            value_providers = {k: v for k, v in value_providers.items() if k not in exclude_columns}

        if objects is None:
            if not value_providers:
                raise Exception('value providers not found')
        else:
            if should_insert:
                objects = [o for o in objects if should_insert(o)]
            if not objects:
                return [] if returns_id or returns_record else 0

        specified_columns = True
        columns = tuple(value_providers)
        if objects:
            if include_attributes:
                columns += tuple(a for a in include_attributes if a not in exclude_columns and a not in columns)
            elif include_attributes is None:
                some_object = next(iter(objects))
                if isinstance(some_object, Entity):
                    columns += tuple(k for k in some_object if k not in exclude_columns and k not in columns and k != '_key_')
                elif isinstance(some_object, dict):
                    columns += tuple(k for k in some_object if k not in exclude_columns and k not in columns)
                elif not columns:
                    columns = tuple(range(len(some_object)))
                    specified_columns = False

        def get_rows_values():
            if objects is not None:
                for column in columns:
                    if column in value_providers:
                        value_provider = value_providers[column]
                        if not inspect.isfunction(value_provider) and not isinstance(value_provider, functools.partial):
                            value_providers[column] = ConstValueProvider(value_provider)
                        else:
                            value_providers[column] = FunctionValueProvider(value_provider)
                    else:
                        value_providers[column] = DictValueProvider(column if specified_columns else columns.index(column))
                for o in objects:
                    yield [value_providers[column](o) for column in columns]
            else:
                yield [value_providers[column] for column in columns]

        fragments = ['INSERT INTO ', table]
        if conflict_target or conflict_action:
            fragments.append(' AS C')  # means "CURRENT"
        if specified_columns:
            fragments.append(' ({})'.format(', '.join(columns)))
        fragments.append(' VALUES ')
        arg_index = 0
        args = {}
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
                arg_index += 1
                arg_name = ''.join(('a', unicode(arg_index)))
                fragments.append('%({})s'.format(arg_name))
                args[arg_name] = column_value
            fragments.append(')')
        if conflict_target or conflict_action:
            fragments.append(' ON CONFLICT {} {}'.format(conflict_target, conflict_action))
        if returns_id:
            if returns_id is True:
                key_names = ('id', )
            elif isinstance(returns_id, basestring):
                key_names = (returns_id, )
            else:
                key_names = returns_id
            fragments.append(' RETURNING {}'.format(', '.join(key_names)))
            if len(key_names) == 1:
                if objects:
                    return self.list_scalar(''.join(fragments), **args)
                else:
                    return self.get_scalar(''.join(fragments), **args)
            else:
                if objects:
                    return self.list(''.join(fragments), returns_dict_object=False, **args)
                else:
                    return self.get(''.join(fragments), returns_dict_object=False, **args)
        elif returns_record:
            fragments.append(' RETURNING {}'.format('*' if returns_record is True else ', '.join(returns_record)))
            if objects:
                return self.list(''.join(fragments), returns_entity=returns_entity, **args)
            else:
                return self.get(''.join(fragments), returns_entity=returns_entity, **args)
        else:
            return self.execute(''.join(fragments), **args)

    def iter_in_batch(self, sql, batch_size=1, db_fetch_size=None, **kwargs):
        """
        batch_size: the number of rows to iterate at a time
        db_fetch_size: the number of rows to fetch from the db server at each network round-trip during iteration on a named cursor
        """
        return self._query_large_result_set(sql, batch_size, db_fetch_size, **kwargs)

    def iter_scalar_in_batch(self, sql, batch_size=1, db_fetch_size=None, **kwargs):
        return self.iter_in_batch(sql, batch_size, db_fetch_size, returns_scalar=True, **kwargs)

    def _execute(self, sql, **kwargs):
        check_table_dependencies(self.component_name, self.purpose, sql)
        reconnected = False
        within_transaction_context = not self.autocommit
        while True:
            with closing(self.conn.cursor(returns_dict_object=False)) as cursor:
                try:
                    cursor.execute(sql, kwargs)
                except Exception as e:
                    if reconnected:
                        LOGGER.exception('failed to execute statement: sql is %(sql)s and kwargs are %(kwargs)s', {
                            'sql': sql,
                            'kwargs': kwargs
                        })
                        raise
                    else:
                        reconnected = self.conn.reconnect_if_broken_per_exception(e)
                        if not reconnected:
                            LOGGER.exception('failed to execute statement: sql is %(sql)s and kwargs are %(kwargs)s', {
                                'sql': sql,
                                'kwargs': kwargs
                            })
                            raise
                        elif within_transaction_context:
                            raise ReconnectedWithinTransactionException()
                else:
                    return cursor.rowcount

    def _executemany(self, sql, seq_of_parameters):
        check_table_dependencies(self.component_name, self.purpose, sql)
        reconnected = False
        within_transaction_context = not self.autocommit
        while True:
            with closing(self.conn.cursor(returns_dict_object=False)) as cursor:
                try:
                    cursor.executemany(sql, seq_of_parameters)
                except Exception as e:
                    if reconnected:
                        LOGGER.exception('failed to executemany statement: sql is %(sql)s and seq_of_parameters are %(seq_of_parameters)s', {
                            'sql': sql,
                            'seq_of_parameters': seq_of_parameters
                        })
                        raise
                    else:
                        reconnected = self.conn.reconnect_if_broken_per_exception(e)
                        if not reconnected:
                            LOGGER.exception('failed to executemany statement: sql is %(sql)s and seq_of_parameters are %(seq_of_parameters)s', {
                                'sql': sql,
                                'seq_of_parameters': seq_of_parameters
                            })
                            raise
                        elif within_transaction_context:
                            raise ReconnectedWithinTransactionException()
                else:
                    return cursor.rowcount

    def _query(self, sql, returns_dict_object=True, returns_entity=False, **kwargs):
        check_table_dependencies(self.component_name, self.purpose, sql)
        reconnected = False
        within_transaction_context = not self.autocommit
        while True:
            with closing(self.conn.cursor(returns_dict_object=returns_dict_object, returns_entity=returns_entity)) as cursor:
                try:
                    cursor.execute(sql, kwargs)
                except Exception as e:
                    if reconnected:
                        LOGGER.exception('failed to execute query: sql is %(sql)s and kwargs are %(kwargs)s', {
                            'sql': sql,
                            'kwargs': kwargs
                        })
                        raise
                    else:
                        reconnected = self.conn.reconnect_if_broken_per_exception(e)
                        if not reconnected:
                            LOGGER.exception('failed to execute query: sql is %(sql)s and kwargs are %(kwargs)s', {
                                'sql': sql,
                                'kwargs': kwargs
                            })
                            raise
                        elif within_transaction_context:
                            raise ReconnectedWithinTransactionException()
                else:
                    return cursor.fetchall()

    def _query_large_result_set(self, sql, batch_size, db_fetch_size, returns_scalar=False, returns_dict_object=True, returns_entity=False, **kwargs):
        """
        Run a query with potentially large result set using server-side cursor
        """
        check_table_dependencies(self.component_name, self.purpose, sql)
        if returns_dict_object and returns_scalar:
            returns_dict_object = False
        reconnected = False
        within_transaction_context = not self.autocommit
        while True:
            try:
                # psycopg2 named cursor is implemented as 'DECLARE name CURSOR WITHOUT HOLD FOR query'
                # and should be within a transaction and not be used in autocommit mode
                with require_transaction_context(self):
                    cursor = self.conn.cursor(name=self._unique_cursor_name(), returns_dict_object=returns_dict_object, returns_entity=returns_entity)
                    if db_fetch_size:
                        cursor.itersize = db_fetch_size
                    cursor.execute(sql, kwargs)
                    rows = cursor.fetchmany(batch_size)
                    while len(rows) > 0:
                        yield [row[0] for row in rows] if returns_scalar else rows
                        rows = cursor.fetchmany(batch_size)
                    cursor.close()
                    # if exception happen before close, the whole transaction should be rolled back by the caller
                    # if we close the cursor when sql execution error, the actual error will be covered by unable to close cursor itself
            except Exception as e:
                if reconnected:
                    LOGGER.exception('failed to query large result set: sql is %(sql)s and kwargs are %(kwargs)s', {
                        'sql': sql,
                        'kwargs': kwargs
                    })
                    raise
                else:
                    reconnected = self.conn.reconnect_if_broken_per_exception(e)
                    if not reconnected:
                        LOGGER.exception('failed to query large result set: sql is %(sql)s and kwargs are %(kwargs)s', {
                            'sql': sql,
                            'kwargs': kwargs
                        })
                        raise
                    elif within_transaction_context:
                        raise ReconnectedWithinTransactionException()
            else:
                break

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


class DictValueProvider(object):
    def __init__(self, key):
        self.key = key

    def __call__(self, obj):
        return obj[self.key]


@event(EVENT_PROCESS_TEARDOWN)
def close_all_connections():
    for purpose, instance in instances.items():
        if not VEIL_ENV.is_test:
            LOGGER.debug('close connection at exit: %(purpose)s', {'purpose': purpose})
        try:
            instance.close()
        except Exception:
            LOGGER.exception('Cannot close database connection')


class ReconnectedWithinTransactionException(Exception):
    pass
