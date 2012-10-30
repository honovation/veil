import veil_component

with veil_component.init_component(__name__):
    from .clock import require_current_time_being
    from .clock import get_current_time
    from .clock import get_current_timestamp

    __all__ = [
        # from clock
        require_current_time_being.__name__,
        get_current_time.__name__,
        get_current_timestamp.__name__
    ]