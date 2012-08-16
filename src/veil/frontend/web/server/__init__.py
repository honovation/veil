import sandal.component

with sandal.component.init_component(__name__):
    from .website import start_website
    from .website import start_test_website
    from .website import create_website_http_handler
    from .routing import route
    from .routing import async_route
    from .routing import public_route
    from .routing import is_public_route
    from .xsrf import xsrf_token

    __all__ = [
        # from website
        start_website.__name__,
        start_test_website.__name__,
        create_website_http_handler.__name__,
        # from routing
        route.__name__,
        async_route.__name__,
        public_route.__name__,
        is_public_route.__name__,
        # from xsrf
        xsrf_token.__name__
    ]

    def init():
        from static_file import process_javascript_and_stylesheet_tags
        from veil.frontend.template import register_page_post_processor

        register_page_post_processor(process_javascript_and_stylesheet_tags)