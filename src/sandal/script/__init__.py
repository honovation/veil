######## export begin
from .script import script
from .script import execute_script

__all__ = [
    # from script
    script.__name__,
    execute_script.__name__
]
######## export end

def init():
    from sandal.component import init_component

    init_component(__name__)

init()