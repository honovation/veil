from veil_installer import *

import veil_component
with veil_component.init_component(__name__):
    from .tenpay_payment import EVENT_TENPAY_TRADE_PAID
    from .tenpay_payment import NOTIFIED_FROM_RETURN_URL
    from .tenpay_payment import NOTIFIED_FROM_NOTIFY_URL
    from .tenpay_payment import create_tenpay_payment_url
    from .tenpay_payment import process_tenpay_payment_notification
    from .tenpay_payment import query_tenpay_payment_status

    from .tenpay_refund import refund
    from .tenpay_refund import query_refund_status
    from .tenpay_refund import process_refund_notification
    from .tenpay_refund import EVENT_TENPAY_REFUND_NOTIFIED
    from .tenpay_refund import TENPayRefundException

    from .tenpay_client_installer import tenpay_client_resource
    from .tenpay_client_installer import tenpay_client_config

    def init():
        add_application_sub_resource('tenpay_client', lambda config: tenpay_client_resource(**config))

    __all__ = [
        'EVENT_TENPAY_TRADE_PAID',
        'NOTIFIED_FROM_RETURN_URL',
        'NOTIFIED_FROM_NOTIFY_URL',
        create_tenpay_payment_url.__name__,
        process_tenpay_payment_notification.__name__,
        query_tenpay_payment_status.__name__,

        refund.__name__,
        query_refund_status.__name__,
        process_refund_notification.__name__,
        'EVENT_TENPAY_REFUND_NOTIFIED',
        'TENPayRefundException',

        tenpay_client_resource.__name__,
        tenpay_client_config.__name__,
    ]