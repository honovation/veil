import veil.component

with veil.component.init_component(__name__):
    from .browser import start_website_and_browser

    __all__ = [
        start_website_and_browser.__name__
    ]

    def init():
        from veil.environment.setting import add_settings
        from .browser_test import TEST_WEBSITE_SETTINGS

        add_settings(TEST_WEBSITE_SETTINGS)