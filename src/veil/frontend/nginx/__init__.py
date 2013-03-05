import veil_component

with veil_component.init_component(__name__):
    from .nginx_installer import nginx_resource

    VEIL_USER_CODE_COOKIE_NAME = 'vucode' # used in nginx access log
    VEIL_BROWSER_CODE_COOKIE_NAME = 'vbcode' # used in nginx access log
    X_REQUEST_CODE_HEADER_NAME = 'X-Request-Code' # used in nginx access log

    __all__ = [
        nginx_resource.__name__,
        'VEIL_USER_CODE_COOKIE_NAME',
        'VEIL_BROWSER_CODE_COOKIE_NAME',
        'X_REQUEST_CODE_HEADER_NAME'
    ]