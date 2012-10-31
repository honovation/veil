import veil_component

with veil_component.init_component(__name__):
    from .architecture_checker import register_architecture_checker
    from .architecture_checker import check_architecture

    __all__ = [
        register_architecture_checker.__name__,
        check_architecture.__name__
    ]

    def init():
        from veil.development.self_checker import register_self_checker
        from .architecture_checker import check_architecture

        register_self_checker('architecture', check_architecture)