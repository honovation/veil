import veil_component

with veil_component.init_component(__name__):
    from .syslog_server_installer import syslog_server_resource

    __all__ = [
        syslog_server_resource.__name__
    ]