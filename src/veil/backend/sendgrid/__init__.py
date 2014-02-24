import veil_component

with veil_component.init_component(__name__):
    from .sendgrid import send_email
    from .sendgrid_client_installer import sendgrid_client_resource

    __all__ = [
        # from sendgrid
        send_email.__name__,
        # from sendgrid_client_installer
        sendgrid_client_resource.__name__,
    ]