import veil_component

with veil_component.init_component(__name__):
    from .sms_provider_emay import get_emay_smservice_instance
    from .sms_provider_yunpian import get_yunpian_smservice_instance
    from .sms import send_transactional_sms_job
    from .sms import send_slow_transactional_sms_job
    from .sms import send_marketing_sms_job
    from .sms import set_current_sms_provider

    from .emay_sms_client_installer import emay_sms_client_resource

    __all__ = [
        send_transactional_sms_job.__name__,
        send_slow_transactional_sms_job.__name__,
        send_marketing_sms_job.__name__,

        emay_sms_client_resource.__name__,
    ]

    def init():
        from .sms import register_sms_provider

        register_sms_provider(get_emay_smservice_instance())
        # register_sms_provider(get_yunpian_smservice_instance())

        set_current_sms_provider()
