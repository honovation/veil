######## export begin
from .case import TestCase
from .case import get_executing_test
from .case import test_hook
from .runner import profile_package
from .runner import test_package

__all__ = [
    # from case
    TestCase.__name__,
    get_executing_test.__name__,
    test_hook.__name__,
    # from runner
    profile_package.__name__,
    test_package.__name__
]
######## export end

def init():
    from sandal.component import init_component

    init_component(__name__)

init()