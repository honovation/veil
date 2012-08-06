from __future__ import unicode_literals, print_function, division
import functools
import inspect
import traceback
from contextlib import contextmanager, closing
from functools import wraps
from logging import getLogger
import uuid
from veil.environment.runtime import register_option
from ..postgresql import PostgresqlAdapter

LOGGER = getLogger(__name__)

registry = {} # purpose => open_database
connected_databases = {} # purpose => database or category => database or __default__ => database

def register_database(purpose):
    section_name = '{}_database'.format(purpose) # for example contact_index_database
    get_db_type = register_option(section_name, 'type')
    get_db_host = register_option(section_name, 'host')
    get_db_port = register_option(section_name, 'port', int)
    get_db_database = register_option(section_name, 'database')
    get_db_user = register_option(section_name, 'user')
    get_db_password = register_option(section_name, 'password')

    def connect_database_if_not_connected():
        if connected_databases.get(purpose):
            return connected_databases[purpose]
        connected_databases[purpose] = connect(
            purpose=purpose,
            type=get_db_type(),
            host=get_db_host(),
            port=get_db_port(),
            database=get_db_database(),
            user=get_db_user(),
            password=get_db_password())
        return connected_databases[purpose]

    registry[purpose] = connect_database_if_not_connected
    return lambda: require_database(purpose)


def require_database(purpose):
    # connect and set the current schema as search path
    if purpose not in registry:
        raise Exception('database for purpose {} is not registered'.format(purpose))
    return registry[purpose]()


def close_databases():
    for database in connected_databases.values():
        database.close()
    connected_databases.clear()


def connect(purpose, type, host, port, database, user, password):
    if 'postgresql' == type:
        adapter = PostgresqlAdapter(
            host=host, port=port,
            database=database, user=user, password=password)
        db = Database(purpose, adapter)
        db.database= database
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
        self.last_sql = None

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
        rows = self._query(sql, returns_named_tuple=False, **kwargs)
        if rows and len(rows[0]) > 1:
            raise Exception('More than one columns returned with the sql: {}'.format(self.last_sql))
        return [row[0] for row in rows]

    def get(self, sql, **kwargs):
        rows = self._query(sql, **kwargs)
        if not rows:
            LOGGER.debug('No rows returned with the sql: {}'.format(self.last_sql))
            return None
        if len(rows) > 1:
            LOGGER.warning('More than one rows returned with the sql: {}'.format(self.last_sql))
        return rows[0]

    def get_scalar(self, sql, **kwargs):
        rows = self._query(sql, returns_named_tuple=False, **kwargs)
        if not rows:
            LOGGER.debug('No rows returned with the sql: {}'.format(self.last_sql))
            return None
        if len(rows) > 1:
            LOGGER.warning('More than one rows returned with the sql: {}'.format(self.last_sql))
        if len(rows[0]) > 1:
            raise Exception('More than one columns returned with the sql: {}'.format(self.last_sql))
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
        with closing(self.conn.cursor(returns_named_tuple=False)) as cursor:
            try:
                cursor.execute(sql, kwargs)
            except:
                LOGGER.error('failed to execute {} with {}'.format(sql, kwargs))
                raise
            self.last_sql = self.conn.get_last_sql(cursor)
            return cursor.rowcount

    def _executemany(self, sql, seq_of_parameters):
        with closing(self.conn.cursor(returns_named_tuple=False)) as cursor:
            try:
                cursor.executemany(sql, seq_of_parameters)
            except:
                LOGGER.error('failed to execute {} with {}'.format(sql, seq_of_parameters))
                raise
            self.last_sql = self.conn.get_last_sql(cursor)
            return cursor.rowcount

    def _query(self, sql, returns_named_tuple=True, **kwargs):
        with closing(self.conn.cursor(returns_named_tuple=returns_named_tuple)) as cursor:
            try:
                cursor.execute(sql, kwargs)
            except:
                LOGGER.error('failed to execute {} with {}'.format(sql, kwargs))
                raise
            self.last_sql = self.conn.get_last_sql(cursor)
            return cursor.fetchall()

    def _query_large_result_set(self, sql, batch_size, db_fetch_size, returns_named_tuple=True, **kwargs):
        """
        Run a query with potentially large result set using server-side cursor
        """
        # psycopg2 named cursor is implemented as 'DECLARE name CURSOR WITHOUT HOLD FOR query' and should be within a transaction and not be used in autocommit mode
        with require_transaction_context(self):
            cursor = self.conn.cursor(name=self._unique_cursor_name(), returns_named_tuple=returns_named_tuple)
            if db_fetch_size:
                cursor.itersize = db_fetch_size
            cursor.execute(sql, kwargs)
            self.last_sql = self.conn.get_last_sql(cursor)
            rows = cursor.fetchmany(batch_size)
            while len(rows) > 0:
                yield rows
                rows = cursor.fetchmany(batch_size)
            cursor.close()
            # if exception happen before close, the whole transaction should be rolled back by the caller
            # if we close the cursor when sql execution error, the actuall error will be covered by unable to close cursor itself

    def set_current_schema(self, schema):
        self.conn.set_current_schema(schema)

    def reset_current_schema(self):
        self.conn.reset_current_schema()

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


class ConstValueProvider(object):
    def __init__(self, const):
        self.const = const

    def __call__(self, obj):
        return self.const