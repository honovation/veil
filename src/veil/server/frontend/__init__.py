import veil_component
with veil_component.init_component(__name__):

    from .frontend import frontend_static_resource

    __all__ = [
        frontend_static_resource.__name__,
    ]
