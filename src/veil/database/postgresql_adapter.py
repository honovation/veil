from __future__ import unicode_literals, print_function, division
from contextlib import closing
from logging import getLogger
import psycopg2
from psycopg2.extensions import  ISOLATION_LEVEL_READ_COMMITTED
from psycopg2.extras import NamedTupleCursor
from psycopg2.extensions import cursor as NormalCursor

LOGGER = getLogger(__name__)

psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

class PostgresqlAdapter(object):
    def __init__(self, host, port, database, user, password):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.conn = self._get_conn()

    def _get_conn(self):
        conn = None
        try:
            conn = psycopg2.connect(
                host=self.host, port=self.port, database=self.database,
                user=self.user, password=self.password)
            conn.set_session(isolation_level=ISOLATION_LEVEL_READ_COMMITTED, autocommit=True)
        except:
            LOGGER.critical('Cannot connect to database', exc_info=1)
            try:
                raise
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except:
                        LOGGER.exception('Cannot close database connection')
        else:
            return conn

    def _reconnect_when_needed(self):
        if self.conn.closed:
            LOGGER.warn('Detected database connection had been closed, reconnect now')
            self.conn = self._get_conn()

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
        if not self.conn.closed:
            self.conn.close()

    def cursor(self, returns_named_tuple=True, **kwargs):
        self._reconnect_when_needed()
        cursor_factory = NamedTupleCursor if returns_named_tuple else NormalCursor
        return self.conn.cursor(cursor_factory=cursor_factory, **kwargs)

    def get_last_sql(self, cursor):
        return cursor.query

    def set_current_schema(self, schema):
        with closing(self.cursor()) as c:
            c.execute('SET search_path TO {}'.format(schema))

    def reset_current_schema(self):
        self.set_current_schema('public')

    def __repr__(self):
        return 'Postgresql adapter {} with connection parameters {}'.format(
            self.__class__.__name__, dict(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user))