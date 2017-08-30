import veil_component
with veil_component.init_component(__name__):
    from .nginx_installer import nginx_resource

    X_REQUEST_CODE_HEADER_NAME = 'X-Request-Code'  # used in nginx access log
    VEIL_BROWSER_CODE_COOKIE_NAME = 'vb'  # used in nginx access log
    VEIL_USER_CODE_COOKIE_NAME = 'vu'  # used in nginx access log

    __all__ = [
        nginx_resource.__name__,
        'X_REQUEST_CODE_HEADER_NAME',
        'VEIL_BROWSER_CODE_COOKIE_NAME',
        'VEIL_USER_CODE_COOKIE_NAME',
    ]