import veil_component
from veil_installer import *

with veil_component.init_component(__name__):
    from .hash import encode_token
    from .hash import decode_token
    from .hash import get_password_hash
    from .hash import get_hmac
    from .hash import verify_hmac
    from .hash import get_check_code
    from .hash import verify_check_code
    from .hash import hash_resource

    def init():
        add_application_sub_resource('hash', lambda config: hash_resource(**config))

    __all__ = [
        # from hash
        encode_token.__name__,
        decode_token.__name__,
        get_password_hash.__name__,
        get_hmac.__name__,
        verify_hmac.__name__,
        get_check_code.__name__,
        verify_check_code.__name__,
        hash_resource.__name__
    ]