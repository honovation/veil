import veil_component

with veil_component.init_component(__name__):
    from .wxpay_payment import get_wxpay_request
    from .wxpay_payment import process_wxpay_payment_notification
    from .wxpay_payment import EVENT_WXPAY_TRADE_PAID
    from .wxpay_payment import NOTIFIED_FROM_RETURN_URL
    from .wxpay_payment import NOTIFIED_FROM_NOTIFY_URL
    from .wxpay_client_installer import wxpay_client_resource
    from .wxpay_client_installer import wxpay_client_config


    __all__ = [
        # from wxpay_trade
        get_wxpay_request.__name__,
        process_wxpay_payment_notification.__name__,
        'EVENT_WXPAY_TRADE_PAID',
        'NOTIFIED_FROM_RETURN_URL',
        'NOTIFIED_FROM_NOTIFY_URL',
        # from wxpay_client_installer
        wxpay_client_resource.__name__,
        wxpay_client_config.__name__,
    ]