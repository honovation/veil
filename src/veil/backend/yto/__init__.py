from veil_installer import *

import veil_component
with veil_component.init_component(__name__):

    from .yto import subscribe_logistics_notify as subscribe_yto_logistics_notify
    from .yto import query_logistics_status as query_yto_logistics_status
    from .yto import EVENT_YTO_LOGISTICS_NOTIFICATION_RECEIVED
    from .yto import YTO_INCOMING_REQUEST_LOG_DIRECTORY_BASE
    from .yto import process_logistics_notification as process_yto_logistics_notification

    from .yto_client_installer import yto_client_resource
    from .yto_client_installer import yto_client_config

    def init():
        add_application_sub_resource('yto_client', lambda config: yto_client_resource(**config))

    __all__ = [
        'subscribe_yto_logistics_notify',
        'query_yto_logistics_status',
        'EVENT_YTO_LOGISTICS_NOTIFICATION_RECEIVED',
        'YTO_INCOMING_REQUEST_LOG_DIRECTORY_BASE',
        'process_yto_logistics_notification',

        yto_client_resource.__name__,
        yto_client_config.__name__,
    ]
