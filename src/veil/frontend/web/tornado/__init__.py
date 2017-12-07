import veil_component
with veil_component.init_component(__name__):
    veil_component.configure_logging('tornado.application')  # clear log handlers and add a human-readable handler which logs to stdout

    from .context import get_current_http_context
    from .context import get_current_http_request
    from .context import get_current_http_response

    from .server import start_http_server
    from .server import start_test_http_server
    from .server import create_stack_context
    from .server import set_http_status_code

    from .error import HTTPError
    from .error import end_http_request_processing

    from .cookie import get_secure_cookie
    from .cookie import set_secure_cookie
    from .cookie import get_cookie
    from .cookie import set_cookie
    from .cookie import clear_cookie
    from .cookie import get_cookies
    from .cookie import clear_cookies
    from .cookie import CreateCookieError

    from .flash_message import set_flash_message
    from .flash_message import clear_and_return_flash_message

    from .redirection import redirect_to

    from .argument import get_http_argument
    from .argument import get_http_arguments
    from .argument import get_http_file
    from .argument import get_http_files
    from .argument import delete_http_argument
    from .argument import clear_http_arguments

    from .executor import require_io_loop_executor

    from tornado.ioloop import IOLoop

    __all__ = [
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
        CreateCookieError.__name__,

        set_flash_message.__name__,
        clear_and_return_flash_message.__name__,

        redirect_to.__name__,

        get_http_argument.__name__,
        get_http_arguments.__name__,
        get_http_file.__name__,
        get_http_files.__name__,
        delete_http_argument.__name__,
        clear_http_arguments.__name__,

        require_io_loop_executor.__name__,

        IOLoop.__name__
    ]