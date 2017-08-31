import veil_component
with veil_component.init_component(__name__):
    from .supervisor_launcher import EVENT_SUPERVISOR_TO_BE_DOWN

    from .supervisorctl import supervisorctl

    from .supervisor_installer import supervisor_resource

    __all__ = [
        'EVENT_SUPERVISOR_TO_BE_DOWN',

        supervisorctl.__name__,

        supervisor_resource.__name__
    ]
