import veil_component

with veil_component.init_component(__name__):
    from .case import TestCase
    from .case import get_executing_test
    from .case import test_hook
    from .fixture import fixture
    from unittest import skip

    __all__ = [
        # from case
        TestCase.__name__,
        get_executing_test.__name__,
        test_hook.__name__,
        # from fixture
        fixture.__name__,
        # from unittest
        skip.__name__
    ]

    def init():
        from veil.development.self_checker import register_self_checker
        from .correctness_checker import check_correctness

        register_self_checker('correctness', check_correctness)