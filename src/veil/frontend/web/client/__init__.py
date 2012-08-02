import sandal.component

with sandal.component.init_component(__name__):
    from .browser import start_website_and_browser

    __all__ = [
        # from browser
        start_website_and_browser.__name__
    ]
