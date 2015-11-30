import veil_component

with veil_component.init_component(__name__):
    from .region import list_region_name_patterns
    from .region import parse_full_address
    __all__ = [
        list_region_name_patterns.__name__,
        parse_full_address.__name__,
    ]