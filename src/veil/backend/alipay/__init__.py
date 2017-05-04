import veil_component
from veil_installer import *

with veil_component.init_component(__name__):
    from .alipay_payment import EVENT_ALIPAY_TRADE_PAID
    from .alipay_payment import NOTIFIED_FROM_RETURN_URL
    from .alipay_payment import NOTIFIED_FROM_NOTIFY_URL
    from .alipay_payment import create_alipay_payment_url
    from .alipay_payment import create_alipay_wap_payment_url
    from .alipay_payment import process_alipay_payment_notification
    from .alipay_payment import query_alipay_payment_status
    from .alipay_payment import make_alipay_order_str
    from .alipay_payment import verify_alipay_sync_notification
    from .alipay_payment import close_alipay_trade
    from .alipay_payment import refund
    from .alipay_payment import process_refund_notification
    from .alipay_payment import process_dback_notification

    from .alipay_client_installer import alipay_client_resource
    from .alipay_client_installer import alipay_client_config

    def init():
        add_application_sub_resource('alipay_client', lambda config: alipay_client_resource(**config))

    __all__ = [
        'EVENT_ALIPAY_TRADE_PAID',
        'NOTIFIED_FROM_RETURN_URL',
        'NOTIFIED_FROM_NOTIFY_URL',
        create_alipay_payment_url.__name__,
        create_alipay_wap_payment_url.__name__,
        process_alipay_payment_notification.__name__,
        query_alipay_payment_status.__name__,
        make_alipay_order_str.__name__,
        verify_alipay_sync_notification.__name__,
        close_alipay_trade.__name__,
        refund.__name__,
        process_refund_notification.__name__,
        process_dback_notification.__name__,

        alipay_client_resource.__name__,
        alipay_client_config.__name__,
    ]
