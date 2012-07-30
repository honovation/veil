######## export begin
from .path import path

__all__ = [
    # from path
    path.__name__
]
######## export end

def init():
    from veil.component import init_component

    init_component(__name__)

init()