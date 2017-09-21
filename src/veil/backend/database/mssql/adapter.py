# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import contextlib
import logging
import re
import pymssql
from pymssql import OperationalError, InterfaceError, InternalError

from veil.utility.encoding import *
from veil.model.collection import *
from veil.backend.database.client import *

LOGGER = logging.getLogger(__name__)


class MSSQLAdapter(object):
    type = DATABASE_TYPE_MSSQL

    def __init__(self, host, port, database, user, password, schema):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.schema = schema  # not supported
        self.conn = self._get_conn()
        assert self.autocommit, 'autocommit should be enabled by default'

    def _get_conn(self):
        conn = None
        connect_args = DictObject(server=self.host, port=self.port, database=self.database, user=self.user, password=self.password, autocommit=True)
        try:
            conn = pymssql.connect(**connect_args)
        except Exception:
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
            with contextlib.closing(self.conn.cursor()) as cur:
                cur.execute(sql)
        except Exception:
            LOGGER.warn('failed in verifying database connection', exc_info=1)
            self._reconnect(depress_exception=False)

    def reconnect_if_broken_per_exception(self, e):
        if isinstance(e, (OperationalError, InterfaceError, InternalError)):
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
        cursor = self.conn.cursor(as_dict=returns_dict_object, **kwargs)
        cursor = NamedParameterCursor(cursor)
        if returns_dict_object:
            return ReturningDictObjectCursor(cursor, returns_entity)
        else:
            return cursor

    def __repr__(self):
        parameters = dict(host=self.host, port=self.port, database=self.database, user=self.user, schema=self.schema)
        return 'MSSQL adapter {} with connection parameters {}'.format(self.__class__.__name__, parameters)


class NamedParameterCursor(object):
    PARAMETER_REGEX = re.compile(r'%\((.*?)\)s')

    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, sql, kwargs=None):
        if not kwargs:
            return self.cursor.execute(sql)
        sql, kwargs_ = self.translate_parameters(sql, kwargs)
        return self.cursor.execute(sql, kwargs_)

    def executemany(self, sql, kwargs=None):
        if not kwargs:
            return self.cursor.executemany(sql)
        sql, kwargs_ = self.translate_parameters(sql, kwargs)
        return self.cursor.executemany(sql, kwargs_)

    def translate_parameters(self, sql, kwargs):
        param_names = []

        def replace_placeholder(match):
            param_name = match.group(1).strip()
            value = kwargs[param_name]
            if param_name not in param_names:
                param_names.append(param_name)
            if isinstance(value, tuple):
                return '({})'.format(', '.join('%({}{})s'.format(param_name, i) for i in range(len(value))))
            else:
                return '%({})s'.format(param_name)

        sql = self.PARAMETER_REGEX.sub(replace_placeholder, sql)
        param_list = [(name, value) for name, value in kwargs.items() if name in param_names and not isinstance(value, tuple)]
        param_list.extend(
            (to_str('{}{}'.format(name, i)), to_str(value))
            for name, values in kwargs.items() if name in param_names and isinstance(values, tuple)
            for i, value in enumerate(values)
        )
        return to_str(sql), dict(param_list)

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        return getattr(self.cursor, attr)


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
        o = DictObject(row)
        return Entity(o, key=None if self.returns_entity is True else self.returns_entity) if self.returns_entity else o

    def __iter__(self):
        while 1:
            yield self.to_dict_object(self.cursor.next())

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        return getattr(self.cursor, attr)
