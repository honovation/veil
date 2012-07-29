from __future__ import unicode_literals, print_function, division
import logging
from veil.environment.runtime import *
from sandal.shell import *
from veil.script import *
from veil.environment.layout import VEIL_HOME

LOGGER = logging.getLogger(__name__)

@script('create-database')
def create_database(purpose='default'):
    try:
        shell_execute('createdb -h {host} -p {port} -U {user} {database}'.format(
            host=get_option(purpose, 'host'),
            port=get_option(purpose, 'port', int),
            user=get_option(purpose, 'user'),
            database=get_option(purpose, 'database')), capture=True)
    except ShellExecutionError, e:
        if 'already exists' in e.output:
            pass # ignore
        else:
            raise

@script('drop-database')
def drop_database(purpose='default'):
    try:
        shell_execute('dropdb -h {host} -p {port} -U {user} {database}'.format(
            host=get_option(purpose, 'host'),
            port=get_option(purpose, 'port', int),
            user=get_option(purpose, 'user'),
            database=get_option(purpose, 'database')), capture=True)
    except ShellExecutionError, e:
        if 'not exist' in e.output:
            pass # ignore
        else:
            raise

@script('migrate')
def migrate(purpose='default'):
    sql_path = VEIL_HOME / 'db' / purpose / '001-baseline.sql'
    shell_execute('psql -h {host} -p {port} -U {user} -f {sql_path} {database}'.format(
        host=get_option(purpose, 'host'),
        port=get_option(purpose, 'port', int),
        user=get_option(purpose, 'user'),
        database=get_option(purpose, 'database'),
        sql_path=sql_path))

@script('reset')
def reset(purpose='default'):
    drop_database(purpose)
    create_database(purpose)
    migrate(purpose)


def get_option(purpose, key, type=unicode):
    return register_option('{}_database'.format(purpose), key, type)()