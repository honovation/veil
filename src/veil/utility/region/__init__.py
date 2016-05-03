import veil_component

with veil_component.init_component(__name__):
    from .region import REGION_NAMES_IGNORABLE_FROM_ADDRESS
    from .region import get_main_region_name
    from .region import list_candidate_region_names
    from .region import list_region_name_patterns
    from .region import parse_full_address
    __all__ = [
        'REGION_NAMES_IGNORABLE_FROM_ADDRESS',
        get_main_region_name.__name__,
        list_candidate_region_names.__name__,
        list_region_name_patterns.__name__,
        parse_full_address.__name__,
    ]
