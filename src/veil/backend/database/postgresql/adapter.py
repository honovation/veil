from __future__ import unicode_literals, print_function, division
from contextlib import closing
from logging import getLogger
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED
from psycopg2.extras import NamedTupleCursor
from psycopg2.extras import register_uuid
from psycopg2.extensions import cursor as NormalCursor
from psycopg2 import DatabaseError, OperationalError, InterfaceError, InternalError

from veil.model.collection import *
from veil.utility.json import *
from veil.backend.database.client import *

LOGGER = getLogger(__name__)

psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
psycopg2.extensions.register_type(register_uuid())


class CustomJsonAdapter(psycopg2.extras.Json):
    def __init__(self, adapted, dumps=None):
        super(CustomJsonAdapter, self).__init__(adapted, dumps)

    def dumps(self, obj):
        return to_readable_json(obj) if obj.get('readable', True) else to_json(obj)


psycopg2.extensions.register_adapter(dict, CustomJsonAdapter)
psycopg2.extras.register_default_json(globally=True, loads=lambda obj: objectify(from_json(obj)))
psycopg2.extras.register_default_jsonb(globally=True, loads=lambda obj: objectify(from_json(obj)))


class PostgresqlAdapter(object):
    type = DATABASE_TYPE_POSTGRESQL

    def __init__(self, host, port, database, user, password, schema):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.schema = schema
        self.conn = self._get_conn()
        assert self.autocommit, 'autocommit should be enabled by default'

    def _get_conn(self):
        conn = None
        options = '-c search_path={}'.format(self.schema) if self.schema else ''
        try:
            conn = psycopg2.connect(host=self.host, port=self.port, database=self.database, user=self.user,
                                    password=self.password, options=options, connect_timeout=3, keepalives=1,
                                    keepalives_idle=60, keepalives_interval=15, keepalives_count=8)
            conn.set_session(isolation_level=ISOLATION_LEVEL_READ_COMMITTED, autocommit=True)
        except:
            LOGGER.critical('Cannot connect to database: %(parameters)s', {'parameters': self}, exc_info=1)
            try:
                raise
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        LOGGER.exception('Cannot close database connection')
        else:
            return conn

    def reconnect_if_broken_per_verification(self, sql='SELECT 1'):
        try:
            with closing(self.conn.cursor(cursor_factory=NormalCursor)) as cur:
                cur.execute(sql)
        except Exception:
            LOGGER.warn('failed in verifying database connection', exc_info=1)
            self._reconnect(depress_exception=False)

    def reconnect_if_broken_per_exception(self, e):
        if isinstance(e, InternalError) and 'You can drop constraint' in e.message:
            return False
        if isinstance(e, (OperationalError, InterfaceError, InternalError)) \
                or isinstance(e, DatabaseError) and 'could not receive data' in unicode(e.message, errors='replace'):
            return self._reconnect(depress_exception=True)
        return False

    def _reconnect(self, depress_exception):
        LOGGER.info('Reconnect now: %(connection)s', {'connection': self})
        try:
            self.close()
        except Exception:
            LOGGER.exception('Cannot close database connection')
        try:
            self.conn = self._get_conn()
        except Exception:
            if depress_exception:
                LOGGER.exception('failed to reconnect')
                return False
            else:
                raise
        else:
            return True

    @property
    def autocommit(self):
        return self.conn.autocommit

    @autocommit.setter
    def autocommit(self, on_off):
        self.conn.autocommit = on_off

    def rollback_transaction(self):
        self.conn.rollback()

    def commit_transaction(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def cursor(self, returns_dict_object=True, returns_entity=False, **kwargs):
        cursor = self.conn.cursor(cursor_factory=NamedTupleCursor if returns_dict_object else NormalCursor, **kwargs)
        if returns_dict_object:
            return ReturningDictObjectCursor(cursor, returns_entity)
        else:
            return cursor

    def __repr__(self):
        parameters = dict(host=self.host, port=self.port, database=self.database, user=self.user, schema=self.schema)
        return 'Postgresql adapter {} with connection parameters {}'.format(self.__class__.__name__, parameters)


class ReturningDictObjectCursor(object):
    def __init__(self, cursor, returns_entity):
        self.cursor = cursor
        self.returns_entity = returns_entity

    def fetchone(self):
        return self.to_dict_object(self.cursor.fetchone())

    def fetchmany(self, size=None):
        return [self.to_dict_object(row) for row in self.cursor.fetchmany(size)]

    def fetchall(self):
        return [self.to_dict_object(row) for row in self.cursor.fetchall()]

    def to_dict_object(self, row):
        return Entity(row._asdict(), key=None if self.returns_entity is True else self.returns_entity) if self.returns_entity else DictObject(row._asdict())

    def __iter__(self):
        while 1:
            yield self.to_dict_object(self.cursor.next())

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        return getattr(self.cursor, attr)
