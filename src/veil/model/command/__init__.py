######## export begin
from .command import command
from .command import command_for
from .command import InvalidCommand
from .command import CommandError
from .command import NotFoundError

__all__ = [
    # from command
    command.__name__,
    command_for.__name__,
    InvalidCommand.__name__,
    CommandError.__name__,
    NotFoundError.__name__
]
######## export end

def init():
    from sandal.component import init_component

    init_component(__name__)

init()