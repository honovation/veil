import veil_component
with veil_component.init_component(__name__):
    from .script import script
    from .script import execute_script
    from .script import is_script_defined
    from .script import get_executing_script_handler
    from .script import ask_for_confirmation

    __all__ = [
        # from script
        script.__name__,
        execute_script.__name__,
        is_script_defined.__name__,
        get_executing_script_handler.__name__,
        ask_for_confirmation.__name__,
    ]
