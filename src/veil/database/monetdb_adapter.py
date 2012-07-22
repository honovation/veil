from __future__ import unicode_literals, print_function, division
from collections import namedtuple
from contextlib import closing
from logging import getLogger
from sandal.encoding import to_str
try:
    import monetdb.sql
except ImportError:
    pass

LOGGER = getLogger(__name__)

class MonetdbAdapter(object):
    def __init__(self, autocommit=False, **connection_kwargs):
        self.connection_kwargs = connection_kwargs
        self.conn = self.connect(autocommit, **connection_kwargs)

    @classmethod
    def connect(cls, autocommit, host, port, database, user, password):
        return monetdb.sql.connect(
            autocommit=autocommit, hostname=host, port=port, database=database,
            username=user, password=password, use_unicode=True)

    @property
    def autocommit(self):
        return self.conn.autocommit

    @autocommit.setter
    def autocommit(self, on_off):
        self.conn.set_autocommit(on_off)

    def rollback_transaction(self):
        self.conn.rollback()

    def commit_transaction(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def cursor(self, returns_named_tuple=True, **kwargs):
        cursor = self.conn.cursor(**kwargs)
        cursor = UnicodeAwareCursor(cursor)
        if returns_named_tuple:
            return ReturnsNamedTupleCursor(cursor)
        else:
            return cursor

    def get_last_sql(self, cursor):
        return cursor.operation

    def set_current_schema(self, schema):
        with closing(self.cursor()) as c:
            c.execute('SET SCHEMA {}'.format(schema))

    def reset_current_schema(self):
        self.set_current_schema('sys')

    def __repr__(self):
        return 'Monetdb adapter {} with connection parameters {}'.format(
            self.__class__.__name__, self.connection_kwargs)


class ReturnsNamedTupleCursor(object):
    Record = None

    def __init__(self, cursor):
        self.cursor = cursor

    def fetchone(self, *args, **kwargs):
        t = self.cursor.fetchone(*args, **kwargs)
        if t is None:
            return None
        else:
            nt = self.Record
            if nt is None:
                nt = self.Record = self._make_nt()
            return nt(*t)

    def fetchmany(self, *args, **kwargs):
        ts = self.cursor.fetchmany(*args, **kwargs)
        nt = self.Record
        if nt is None:
            nt = self.Record = self._make_nt()
        return [nt(*t) for t in ts]

    def fetchall(self, *args, **kwargs):
        ts = self.cursor.fetchall(*args, **kwargs)
        nt = self.Record
        if nt is None:
            nt = self.Record = self._make_nt()
        return [nt(*t) for t in ts]

    def __getattr__(self, item):
        return getattr(self.cursor, item)

    def __getitem__(self, item):
        return self.cursor[item]

    def _make_nt(self):
        return namedtuple("Record", [d[0] for d in self.description or ()])


class UnicodeAwareCursor(object):
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, operation, parameters=None):
        return self.cursor.execute(to_str(operation), parameters)

    def __getattr__(self, item):
        return getattr(self.cursor, item)

    def __getitem__(self, item):
        return self.cursor[item]