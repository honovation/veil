######## export begin
from .fixture import fixtures
from .fixture import register_fixture
from .fixture import fixture
from .fixture import UsingFixture
from .fixture import get_executing_test

__all__ = [
    'fixtures',
    register_fixture.__name__,
    fixture.__name__,
    UsingFixture.__name__,
    get_executing_test.__name__
]
######## export end

def init():
    from sandal.component import init_component

    init_component(__name__)

init()