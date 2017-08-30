from veil_installer import *

import veil_component
with veil_component.init_component(__name__):

    from .zto import query_logistics_status as query_zto_logistics_status
    from .zto import EVENT_ZTO_LOGISTICS_NOTIFICATION_RECEIVED
    from .zto import process_logistics_notification as process_zto_logistics_notification
    from .zto import subscribe_logistics_notify as subscribe_zto_logistics_notify

    from .zto_client_installer import zto_client_resource
    from .zto_client_installer import zto_client_config

    def init():
        add_application_sub_resource('zto_client', lambda config: zto_client_resource(**config))

    __all__ = [
        'query_zto_logistics_status',
        'EVENT_ZTO_LOGISTICS_NOTIFICATION_RECEIVED',
        'process_zto_logistics_notification',
        'subscribe_zto_logistics_notify',

        zto_client_resource.__name__,
        zto_client_config.__name__,
    ]
