import veil.component

with veil.component.init_component(__name__):
    from .launcher import start_website
    from .launcher import start_test_website

    __all__ = [
        start_website.__name__,
        start_test_website.__name__
    ]

    def init():
        from .option import register_website
        from ..routing import register_website_initializer

        register_website_initializer(register_website)