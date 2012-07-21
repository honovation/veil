######## export begin
from .shell import shell_execute
from .shell import pass_control_to

__all__ = [
    # from shell
    shell_execute.__name__,
    pass_control_to.__name__
]
######## export end

def init():
    from sandal.component import init_component

    init_component(__name__)

init()