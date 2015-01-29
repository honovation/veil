import veil_component

with veil_component.init_component(__name__):
    from http import requests
    from http import Retry

    __all__ = [
        requests.__name__,
        Retry.__name__,
    ]
