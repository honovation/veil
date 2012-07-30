######## export begin
from .option import register_option
from .option import init_options
from .option import reset_options
from .option import peek_options
from .bootstrapper import bootstrap_runtime

__all__ = [
    # from option
    register_option.__name__,
    init_options.__name__,
    reset_options.__name__,
    peek_options.__name__,
    # from bootstrapper
    bootstrap_runtime.__name__
]
######## export end

def init():
    from veil.component import init_component

    init_component(__name__)

init()