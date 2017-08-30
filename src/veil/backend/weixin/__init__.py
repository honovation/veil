import veil_component
with veil_component.init_component(__name__):

    from .access_token import get_wxmp_access_token
    from .access_token import refresh_wxmp_access_token

    from .js_api_ticket import refresh_wxmp_jsapi_ticket

    from .js_sdk import get_js_sdk_config

    __all__ = [
        get_wxmp_access_token.__name__,
        refresh_wxmp_access_token.__name__,

        refresh_wxmp_jsapi_ticket.__name__,

        get_js_sdk_config.__name__,
    ]
