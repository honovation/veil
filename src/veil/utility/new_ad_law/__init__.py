import veil_component
with veil_component.init_component(__name__):
    from .new_ad_law import get_new_ad_law_matched_words

    __all__ = [
        get_new_ad_law_matched_words.__name__,
    ]
