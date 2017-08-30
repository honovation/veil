import veil_component
with veil_component.init_component(__name__):
    from .supervisorctl import supervisorctl

    from .supervisor_installer import supervisor_resource

    __all__ = [
        supervisorctl.__name__,

        supervisor_resource.__name__
    ]
