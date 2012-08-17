import veil.component

with veil.component.init_component(__name__):
    from .locale import install_translations

    __all__ = [
        # from locale
        install_translations.__name__
    ]