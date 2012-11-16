import veil_component

with veil_component.init_component(__name__):
    from .architecture_checker import register_architecture_checker
    from .architecture_checker import check_architecture
    from .encapsulation_checker import check_encapsulation

    __all__ = [
        register_architecture_checker.__name__,
        check_architecture.__name__,
        check_encapsulation.__name__
    ]