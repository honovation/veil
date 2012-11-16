import veil_component

with veil_component.init_component(__name__):
    from .loc_checker import check_loc

    __all__ = [
        check_loc.__name__
    ]