import importlib

import veil_component

with veil_component.init_component(__name__):
    from .sms import send_transactional_sms_job
    from .sms import send_voice_validation_code_job
    from .sms import send_slow_transactional_sms_job
    from .sms import send_marketing_sms_job
    from .sms import set_current_sms_provider

    from .sms_provider_emay import emay_sms_client_resource

    from .sms_provider_yunpian import yunpian_sms_client_resource

    __all__ = [
        send_transactional_sms_job.__name__,
        send_voice_validation_code_job.__name__,
        send_slow_transactional_sms_job.__name__,
        send_marketing_sms_job.__name__,

        emay_sms_client_resource.__name__,

        yunpian_sms_client_resource.__name__,
    ]

    def init():
        from veil.environment.environment import get_application
        from .sms import register_sms_provider
        application = get_application()
        if not hasattr(application, 'ENABLED_SMS_PROVIDERS'):
            return
        for provider_name in application.ENABLED_SMS_PROVIDERS:
            provider_module = importlib.import_module('.sms_provider_{}'.format(provider_name).format(name=provider_name), package='veil.backend.sms')
            register_sms_provider(provider_module.register())
