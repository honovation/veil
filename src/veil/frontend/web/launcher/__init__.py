import veil.component

with veil.component.init_component(__name__):
    from .launcher import start_website
    from .launcher import start_test_website
    from .setting import register_website
    from .setting import website_settings
    from .setting import website_program

    __all__ = [
        start_website.__name__,
        start_test_website.__name__,
        register_website.__name__,
        website_settings.__name__,
        website_program.__name__
    ]

    def init():
        from veil.model.event import subscribe_event
        from .setting import register_website
        from ..routing import EVENT_NEW_WEBSITE

        subscribe_event(EVENT_NEW_WEBSITE, register_website)