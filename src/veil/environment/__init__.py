######## export begin
from .layout import VEIL_HOME
from .layout import VEIL_LAYOUT

VEIL_HOME = VEIL_HOME
VEIL_LAYOUT = VEIL_LAYOUT

__all__ = [
    # from home
    'VEIL_HOME',
    'VEIL_LAYOUT'
]
######## export end

def init():
    from sandal.component import init_component

    init_component(__name__)

init()