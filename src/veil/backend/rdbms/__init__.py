######## export begin
from .client import register_database
from .client import transactional
from .postgresql import postgresql_program

__all__ = [
    # from client
    register_database.__name__,
    transactional.__name__,
    # from postgresql
    postgresql_program.__name__
]
######## export end

def init():
    from veil.component import init_component

    init_component(__name__)

init()