import veil_component

with veil_component.init_component(__name__):
    from .wxpay_payment import EVENT_WXPAY_TRADE_PAID
    from .wxpay_payment import NOTIFIED_FROM_ORDER_QUERY
    from .wxpay_payment import NOTIFIED_FROM_NOTIFY_URL
    from .wxpay_payment import get_wxmp_access_token
    from .wxpay_payment import process_wxpay_payment_notification
    from .wxpay_payment import query_wxpay_payment_status
    from .wxpay_payment import make_wxpay_prepay_order
    from .wxpay_payment import get_wx_open_sign

    from .wxpay_client_installer import wxpay_client_resource
    from .wxpay_client_installer import wxpay_client_config
    from .wxpay_client_installer import wx_open_app_resource
    from .wxpay_client_installer import wx_open_app_config

    __all__ = [
        'EVENT_WXPAY_TRADE_PAID',
        'NOTIFIED_FROM_ORDER_QUERY',
        'NOTIFIED_FROM_NOTIFY_URL',
        get_wxmp_access_token.__name__,
        process_wxpay_payment_notification.__name__,
        query_wxpay_payment_status.__name__,
        make_wxpay_prepay_order.__name__,
        get_wx_open_sign.__name__,

        wxpay_client_resource.__name__,
        wxpay_client_config.__name__,
        wx_open_app_resource.__name__,
        wx_open_app_config.__name__,
    ]
