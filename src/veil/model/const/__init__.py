######## export begin
from .const import Consts
from .const import consts
from .const import is_const
from .const import def_const

__all__ = [
    # from const
    Consts.__name__,
    is_const.__name__,
    def_const.__name__,
    'consts'
]
######## export end

def init():
    from veil.component import init_component

    init_component(__name__)

init()