######## export begin
from .layout import VEIL_HOME

VEIL_HOME = VEIL_HOME

__all__ = [
    # from home
    'VEIL_HOME'
]
######## export end

def init():
    from sandal.component import init_component

    init_component(__name__)

init()