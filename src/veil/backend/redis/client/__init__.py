######## export begin
from .client import register_redis

__all__ = [
    # from client
    register_redis.__name__
]
######## export end

def init():
    from veil.component import init_component

    init_component(__name__)

init()