######## export begin
from .server import POSTGRESQL_BASE_SETTINGS
from .client import PostgresqlAdapter

POSTGRESQL_BASE_SETTINGS = POSTGRESQL_BASE_SETTINGS

__all__ = [
    # from server
    'POSTGRESQL_BASE_SETTINGS',
    # from client
    PostgresqlAdapter.__name__
]
######## export end

def init():
    from veil.component import init_component

    init_component(__name__)

init()