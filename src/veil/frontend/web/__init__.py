import veil_component

with veil_component.init_component(__name__):
    from .const import HTML_START_TAG_PREFIX
    from .const import HEAD_END_TAG
    from .const import BODY_END_TAG
    from .website_launcher import start_website
    from .website_launcher import start_test_website
    from .website_launcher import register_website_context_manager
    from .website_installer import get_website_url_prefix
    from .website_installer import get_website_domain
    from .website_installer import get_website_parent_domain
    from .website_installer import website_resource
    from .client import start_website_and_client
    from .routing import route
    from .routing import route_for
    from .routing import async_route
    from .routing import public_route
    from .routing import is_public_route
    from .routing import RoutingHTTPHandler
    from .routing import get_routes
    from .routing import register_page_post_processor
    from .routing import TAG_NO_POST_PROCESS
    from .routing import TAG_NO_LOGIN_REQUIRED
    from .routing import publish_new_website_event
    from .routing import RoutePermissionProtector
    from .routing import TagBasedRoutePermissionProtector
    from .routing import RESOURCE_URI_PREFIX
    from .static_file import static_url
    from .static_file import process_script_elements
    from .tornado import get_current_http_context
    from .tornado import get_current_http_request
    from .tornado import get_current_http_response
    from .tornado import start_http_server
    from .tornado import start_test_http_server
    from .tornado import create_stack_context
    from .tornado import set_http_status_code
    from .tornado import HTTPError
    from .tornado import end_http_request_processing
    from .tornado import get_secure_cookie
    from .tornado import set_secure_cookie
    from .tornado import get_cookie
    from .tornado import set_cookie
    from .tornado import clear_cookie
    from .tornado import get_cookies
    from .tornado import clear_cookies
    from .tornado import redirect_to
    from .tornado import get_http_argument
    from .tornado import get_http_arguments
    from .tornado import get_http_file
    from .tornado import get_http_files
    from .tornado import delete_http_argument
    from .tornado import clear_http_arguments
    from .tornado import require_io_loop_executor
    from .xsrf import xsrf_token
    from .xsrf import TAG_NO_XSRF_CHECK

    __all__ = [
        # from consts
        'HTML_START_TAG_PREFIX',
        'HEAD_END_TAG',
        'BODY_END_TAG',
        # from website
        start_website.__name__,
        start_test_website.__name__,
        register_website_context_manager.__name__,
        # from website_installer
        get_website_url_prefix.__name__,
        get_website_domain.__name__,
        get_website_parent_domain.__name__,
        website_resource.__name__,
        # from client
        start_website_and_client.__name__,
        # from routing
        route.__name__,
        route_for.__name__,
        async_route.__name__,
        public_route.__name__,
        is_public_route.__name__,
        RoutingHTTPHandler.__name__,
        get_routes.__name__,
        register_page_post_processor.__name__,
        'TAG_NO_POST_PROCESS',
        'TAG_NO_LOGIN_REQUIRED',
        publish_new_website_event.__name__,
        RoutePermissionProtector.__name__,
        TagBasedRoutePermissionProtector.__name__,
        'RESOURCE_URI_PREFIX',
        # from static_file
        static_url.__name__,
        process_script_elements.__name__,
        # from tornado
        get_current_http_context.__name__,
        get_current_http_request.__name__,
        get_current_http_response.__name__,
        start_http_server.__name__,
        start_test_http_server.__name__,
        create_stack_context.__name__,
        set_http_status_code.__name__,
        HTTPError.__name__,
        end_http_request_processing.__name__,
        get_secure_cookie.__name__,
        set_secure_cookie.__name__,
        get_cookie.__name__,
        set_cookie.__name__,
        clear_cookie.__name__,
        get_cookies.__name__,
        clear_cookies.__name__,
        redirect_to.__name__,
        get_http_argument.__name__,
        get_http_arguments.__name__,
        get_http_file.__name__,
        get_http_files.__name__,
        delete_http_argument.__name__,
        clear_http_arguments.__name__,
        require_io_loop_executor.__name__,
        # from xsrf
        xsrf_token.__name__,
        'TAG_NO_XSRF_CHECK'
    ]

    def init():
        from veil.frontend.nginx import VEIL_USER_CODE_COOKIE_NAME
        from veil.frontend.nginx import VEIL_BROWSER_CODE_COOKIE_NAME
        from veil.frontend.nginx import X_REQUEST_CODE_HEADER_NAME
        from veil_component import add_log_context_provider

        add_log_context_provider(lambda: {
            'request_code': get_current_http_request().headers.get(X_REQUEST_CODE_HEADER_NAME) if get_current_http_request(optional=True) else '',
            'user_code': get_cookie(VEIL_USER_CODE_COOKIE_NAME) or '',
            'browser_code': get_cookie(VEIL_BROWSER_CODE_COOKIE_NAME) or ''
        })
