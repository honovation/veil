import veil_component

with veil_component.init_component(__name__):
    from .wxpay_payment import get_wxpay_request
    from .wxpay_payment import process_wxpay_payment_notification
    from .wxpay_payment import EVENT_WXPAY_TRADE_PAID
    from .wxpay_payment import NOTIFIED_FROM_ORDER_QUERY
    from .wxpay_payment import NOTIFIED_FROM_NOTIFY_URL
    from .wxpay_payment import query_order_status
    from .wxpay_payment import request_wxmp_access_token
    from .wxpay_payment import send_deliver_notify
    from .wxpay_client_installer import wxpay_client_resource
    from .wxpay_client_installer import wxpay_client_config


    __all__ = [
        # from wxpay_payment
        get_wxpay_request.__name__,
        process_wxpay_payment_notification.__name__,
        'EVENT_WXPAY_TRADE_PAID',
        'NOTIFIED_FROM_ORDER_QUERY',
        'NOTIFIED_FROM_NOTIFY_URL',
        query_order_status.__name__,
        request_wxmp_access_token.__name__,
        send_deliver_notify.__name__,
        # from wxpay_client_installer
        wxpay_client_resource.__name__,
        wxpay_client_config.__name__,
    ]