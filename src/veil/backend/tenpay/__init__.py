import veil_component

with veil_component.init_component(__name__):
    from .tenpay_payment import create_tenpay_payment_url
    from .tenpay_payment import process_tenpay_payment_notification
    from .tenpay_payment import EVENT_TENPAY_TRADE_PAID
    from .tenpay_payment import NOTIFIED_FROM_RETURN_URL
    from .tenpay_payment import NOTIFIED_FROM_NOTIFY_URL
    from .tenpay_client_installer import tenpay_client_resource
    from .tenpay_client_installer import tenpay_client_config


    __all__ = [
        # from tenpay_trade
        create_tenpay_payment_url.__name__,
        process_tenpay_payment_notification.__name__,
        'EVENT_TENPAY_TRADE_PAID',
        'NOTIFIED_FROM_RETURN_URL',
        'NOTIFIED_FROM_NOTIFY_URL',
        # from tenpay_client_installer
        tenpay_client_resource.__name__,
        tenpay_client_config.__name__,
    ]