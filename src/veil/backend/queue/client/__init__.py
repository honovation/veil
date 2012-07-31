######## export begin
from .queue import require_queue

__all__ = [
    # from queue
    require_queue.__name__,
]
######## export end

def init():
    from sandal.component import init_component

    init_component(__name__)

init()