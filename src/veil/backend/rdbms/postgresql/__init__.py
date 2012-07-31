######## export begin
from .client import PostgresqlAdapter
from .server import postgresql_program

__all__ = [
    # from client
    PostgresqlAdapter.__name__,
    # from server
    postgresql_program.__name__
]
######## export end

def init():
    from veil.component import init_component

    init_component(__name__)

init()