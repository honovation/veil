######## export begin
from .adapter import PostgresqlAdapter

__all__ = [
    # from adapter
    PostgresqlAdapter.__name__
]
######## export end

def init():
    from veil.component import init_component

    init_component(__name__)

init()