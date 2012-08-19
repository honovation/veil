import veil.component

with veil.component.init_component(__name__):
    from .browser import browsing
    from .browser import start_website_and_browser
    from .browser import interact_with_page

    __all__ = [
        browsing.__name__,
        start_website_and_browser.__name__,
        interact_with_page.__name__,
    ]

    def init():
        from veil.environment.setting import add_settings
        from .__test__ import TEST_WEBSITE_SETTINGS

        add_settings(TEST_WEBSITE_SETTINGS)