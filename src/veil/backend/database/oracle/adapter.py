# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import contextlib
import logging
import re
import os
import decimal
import cx_Oracle
from cx_Oracle import OperationalError

from veil.utility.encoding import *
from veil.model.collection import *
from veil.backend.database.client import *

LOGGER = logging.getLogger(__name__)


class OracleAdapter(object):
    type = DATABASE_TYPE_ORACLE

    def __init__(self, host, port, database, user, password, schema, timeout):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.schema = schema
        self.timeout = timeout  # TODO: not implemented yet
        self.conn = self._get_conn()
        assert self.autocommit, 'autocommit should be enabled by default'

    def _get_conn(self):
        os.environ['NLS_LANG'] = 'AMERICAN_CHINA.UTF8'
        conn = None
        connection_string = '{}/{}@{}'.format(self.user, self.password, cx_Oracle.makedsn(self.host, self.port, self.database))
        try:
            conn = cx_Oracle.connect(connection_string)
            conn.outputtypehandler = OracleAdapter.output_type_handler
            conn.autocommit = True
            if self.schema:
                conn.current_schema = str(self.schema)  # TODO: current_schema requires str, complains against unicode, may be fixed in new release
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

    @staticmethod
    def output_type_handler(cursor, name, defaultType, size, precision, scale):
        # copy from http://www.oracle.com/technetwork/articles/tuininga-cx-oracle-084866.html
        if defaultType == cx_Oracle.NUMBER and scale > 0:
            return cursor.var(str, 100, cursor.arraysize, outconverter=decimal.Decimal)

    def reconnect_if_broken_per_verification(self, sql='SELECT 1 FROM DUAL'):
        try:
            with contextlib.closing(self.conn.cursor()) as cur:
                cur.execute(sql)
        except Exception:
            LOGGER.warn('failed in verifying database connection', exc_info=1)
            self._reconnect(depress_exception=False)

    def reconnect_if_broken_per_exception(self, e):
        return self._reconnect(depress_exception=True) if isinstance(e, OperationalError) else False

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
        cursor = self.conn.cursor(**kwargs)
        cursor = NamedParameterCursor(cursor)
        if returns_dict_object:
            return ReturningDictObjectCursor(cursor, returns_entity)
        else:
            return cursor

    def __repr__(self):
        parameters = dict(host=self.host, port=self.port, database=self.database, user=self.user, schema=self.schema,
                          timeout=self.timeout)
        return 'Oracle adapter {} with connection parameters {}'.format(self.__class__.__name__, parameters)


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
                return '({})'.format(', '.join(':{}{}'.format(param_name, i) for i in range(len(value))))
            else:
                return ':{}'.format(param_name)

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
        o = DictObject()
        for i, cell in enumerate(row):
            o[self.get_column_name(i)] = cell
        return Entity(o, key=None if self.returns_entity is True else self.returns_entity) if self.returns_entity else o

    def get_column_name(self, i):
        return self.cursor.description[i][0].lower()

    def __iter__(self):
        while 1:
            yield self.to_dict_object(self.cursor.next())

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        return getattr(self.cursor, attr)
