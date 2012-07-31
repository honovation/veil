######## export begin
from .client import register_redis
from .server import redis_program

__all__ = [
    # from client
    register_redis.__name__,
    # from server
    redis_program.__name__
]
######## export end

def init():
    from sandal.component import init_component

    init_component(__name__)

init()