import importlib

import veil_component
with veil_component.init_component(__name__):
    from .sms import send_validation_code_via_sms
    from .sms import send_validation_code_via_voice
    from .sms import send_sms

    from .sms_provider_yunpian import yunpian_sms_client_resource

    from .sms_provider_yuntongxun import yuntongxun_sms_client_resource

    __all__ = [
        send_validation_code_via_sms.__name__,
        send_validation_code_via_voice.__name__,
        send_sms.__name__,

        yunpian_sms_client_resource.__name__,

        yuntongxun_sms_client_resource.__name__,
    ]

    def init():
        from veil.environment.environment import get_application
        from .sms import register_sms_provider
        application = get_application()
        if not hasattr(application, 'ENABLED_SMS_PROVIDERS'):
            return
        for provider_name in application.ENABLED_SMS_PROVIDERS:
            provider_module = importlib.import_module('.sms_provider_{}'.format(provider_name), package=__name__)
            register_sms_provider(provider_module)
