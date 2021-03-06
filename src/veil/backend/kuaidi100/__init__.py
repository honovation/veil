from veil_installer import *

import veil_component
with veil_component.init_component(__name__):
    from .kuaidi100 import get_delivery_status_by_kuaidi100
    from .kuaidi100 import waybill_web_url
    from .kuaidi100 import DELIVERY_STATE_SIGNED
    from .kuaidi100 import DELIVERY_STATE_REJECTED
    from .kuaidi100 import IPBlockedException
    from .kuaidi100 import get_delivery_provider
    from .kuaidi100_client_installer import kuaidi100_client_resource
    def init():
        add_application_sub_resource('kuaidi100_client', lambda config: kuaidi100_client_resource(**config))

    __all__ = [
        # from kuaidi100
        get_delivery_status_by_kuaidi100.__name__,
        get_delivery_provider.__name__,
        waybill_web_url.__name__,
        'DELIVERY_STATE_SIGNED',
        'DELIVERY_STATE_REJECTED',
        IPBlockedException.__name__,
        # from kuaidi100_client_installer
        kuaidi100_client_resource.__name__,
    ]