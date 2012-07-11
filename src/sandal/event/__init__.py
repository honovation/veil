######## export begin
from .event import publish_event
from .event import subscribe_event
from .event import unsubscribe_event

__all__ = [
        publish_event.__name__,
        subscribe_event.__name__,
        unsubscribe_event.__name__
]
######## export end

def init():
    from sandal.component import init_component

    init_component(__name__)

init()