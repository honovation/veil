import veil_component

with veil_component.init_component(__name__):
    from .supervisorctl import supervisorctl
    from .supervisorctl import is_supervisord_running
    from .supervisor_installer import supervisor_resource

    __all__ = [
        supervisorctl.__name__,
        is_supervisord_running.__name__,
        supervisor_resource.__name__
    ]