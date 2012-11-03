import veil_component

with veil_component.init_component(__name__):
    from .checker import register_self_checker

    __all__ = [
        register_self_checker.__name__
    ]

    def init():
        from veil.development.test import check_correctness
        from .checker import register_self_checker

        register_self_checker('correctness', check_correctness)