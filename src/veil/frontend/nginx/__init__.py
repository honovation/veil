import veil_component

with veil_component.init_component(__name__):
    from .nginx_installer import nginx_resource

    VEIL_USER_ID_COOKIE_NAME = 'vuid' # used in nginx access log
    VEIL_BROWSER_CODE_COOKIE_NAME = 'vbcode' # used in nginx access log

    __all__ = [
        nginx_resource.__name__,
        'VEIL_USER_ID_COOKIE_NAME',
        'VEIL_BROWSER_CODE_COOKIE_NAME'
    ]