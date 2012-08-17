import veil.component

with veil.component.init_component(__name__):
    from .launcher import start_website
    from .launcher import start_test_website

    __all__ = [
        start_website.__name__,
        start_test_website.__name__
    ]