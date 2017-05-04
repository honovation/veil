import veil_component
from veil_installer import *

with veil_component.init_component(__name__):
    from .sendgrid import send_email
    from .sendgrid import send_transactional_email_job

    from .sendgrid_client_installer import sendgrid_client_resource

    def init():
        add_application_sub_resource('sendgrid_client', lambda config: sendgrid_client_resource(**config))


    __all__ = [
        # from sendgrid
        send_email.__name__,
        send_transactional_email_job.__name__,
        # from sendgrid_client_installer
        sendgrid_client_resource.__name__,
    ]
