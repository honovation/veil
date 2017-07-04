import veil_component
from veil_installer import *

with veil_component.init_component(__name__):
    from .alipay_client_installer import alipay_client_resource
    from .alipay_client_installer import alipay_client_config

    from .alipay_payment import EVENT_ALIPAY_TRADE_PAID
    from .alipay_payment import create_alipay_pc_payment_url
    from .alipay_payment import create_alipay_wap_payment_url
    from .alipay_payment import make_alipay_app_payment_order_str
    from .alipay_payment import mark_alipay_payment_successful
    from .alipay_payment import query_alipay_payment_status
    from .alipay_payment import close_alipay_payment_trade

    from .alipay_payment_ import NOTIFIED_FROM_RETURN_URL
    from .alipay_payment_ import NOTIFIED_FROM_NOTIFY_URL
    from .alipay_payment_ import create_alipay_payment_url
    from .alipay_payment_ import create_alipay_wap_payment_url_
    from .alipay_payment_ import process_alipay_payment_notification_
    from .alipay_payment_ import query_alipay_payment_status_
    from .alipay_payment_ import make_alipay_order_str
    from .alipay_payment_ import verify_alipay_sync_notification
    from .alipay_payment_ import close_alipay_trade

    from .alipay_refund import refund
    from .alipay_refund import query_refund_status
    from .alipay_refund import ALIPayRefundException

    def init():
        add_application_sub_resource('alipay_client', lambda config: alipay_client_resource(**config))

    __all__ = [
        alipay_client_resource.__name__,
        alipay_client_config.__name__,

        'EVENT_ALIPAY_TRADE_PAID',
        create_alipay_pc_payment_url.__name__,
        create_alipay_wap_payment_url.__name__,
        make_alipay_app_payment_order_str.__name__,
        mark_alipay_payment_successful.__name__,
        query_alipay_payment_status.__name__,
        close_alipay_payment_trade.__name__,

        'NOTIFIED_FROM_RETURN_URL',
        'NOTIFIED_FROM_NOTIFY_URL',
        create_alipay_payment_url.__name__,
        create_alipay_wap_payment_url_.__name__,
        process_alipay_payment_notification_.__name__,
        query_alipay_payment_status_.__name__,
        make_alipay_order_str.__name__,
        verify_alipay_sync_notification.__name__,
        close_alipay_trade.__name__,

        refund.__name__,
        query_refund_status.__name__,
        'ALIPayRefundException',
    ]
