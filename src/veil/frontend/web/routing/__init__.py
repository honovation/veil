import veil_component

with veil_component.init_component(__name__):
    from .routing import route
    from .routing import route_for
    from .routing import async_route
    from .routing import public_route
    from .routing import is_public_route
    from .routing import RoutingHTTPHandler
    from .routing import get_routes
    from .routing import EVENT_NEW_WEBSITE
    from .routing import publish_new_website_event
    from .page_post_processor import register_page_post_processor
    from .page_post_processor import TAG_NO_POST_PROCESS

    __all__ = [
        # from routing
        route.__name__,
        route_for.__name__,
        async_route.__name__,
        public_route.__name__,
        is_public_route.__name__,
        RoutingHTTPHandler.__name__,
        get_routes.__name__,
        'EVENT_NEW_WEBSITE',
        publish_new_website_event.__name__,
        # from page_post_processor
        register_page_post_processor.__name__,
        'TAG_NO_POST_PROCESS'
    ]