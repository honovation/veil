from __future__ import unicode_literals, print_function, division
from contextlib import closing
from logging import getLogger
import ibm_db_dbi
from veil.model.collection import *

LOGGER = getLogger(__name__)

class DB2Adapter(object):
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
            conn = ibm_db_dbi.connect(
                'DRIVER={IBM DB2 ODBC DRIVER};DATABASE=%s;HOSTNAME=%s;PORT=%s; PROTOCOL=TCPIP;UID=%s;PWD=%s;' %
                (self.database, self.host, self.port, self.user, self.password))
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
        pass

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

    def cursor(self, returns_dict_object=True, **kwargs):
        self._reconnect_when_needed()
        cursor = self.conn.cursor(**kwargs)
        if returns_dict_object:
            return ReturningDictObjectCursor(cursor)
        else:
            return cursor

    def set_current_schema(self, schema):
        with closing(self.cursor()) as c:
            c.execute('SET search_path TO {}'.format(schema))

    def reset_current_schema(self):
        self.set_current_schema('public')

    def __repr__(self):
        return 'DB2 adapter {} with connection parameters {}'.format(
            self.__class__.__name__, dict(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user))


class ReturningDictObjectCursor(object):
    def __init__(self, cursor):
        self.cursor = cursor

    def fetchone(self):
        return self.to_dict_object(self.cursor.fetchone())

    def fetchmany(self, size=None):
        return [self.to_dict_object(row) for row in self.cursor.fetchmany(size)]

    def fetchall(self):
        return [self.to_dict_object(row) for row in self.cursor.fetchall()]

    def to_dict_object(self, row):
        o = DictObject()
        for i, cell in enumerate(row):
            o[self.get_column_name(i)] = cell
        return o

    def get_column_name(self, i):
        return self.cursor.description[i][0].lower()

    def __iter__(self):
        while 1:
            yield self.to_dict_object(self.cursor.next())

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        return getattr(self.cursor, attr)