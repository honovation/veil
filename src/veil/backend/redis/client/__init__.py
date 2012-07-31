######## export begin
from .client import register_redis

__all__ = [
    # from client
    register_redis.__name__
]
######## export end

def init():
    from sandal.component import init_component

    init_component(__name__)

init()