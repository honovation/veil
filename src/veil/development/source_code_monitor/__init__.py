import veil_component

with veil_component.init_component(__name__):
    from .reloader import register_reloads_on_change_group
    from .reloader import register_reloads_on_change_program

    __all__ = [
        register_reloads_on_change_group.__name__,
        register_reloads_on_change_program.__name__
    ]