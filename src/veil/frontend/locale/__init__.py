######## export begin
from .i18n import require_current_locale_being
from .i18n import require_current_locale_being_default
from .i18n import load_translations
from .i18n import get_locale
from .i18n import get_current_locale
from .i18n import get_default_locale
from .i18n import _
from .i18n import install_null_translation

__all__ = [
        # from i18n
        require_current_locale_being.__name__,
        require_current_locale_being_default.__name__,
        load_translations.__name__,
                get_locale.__name__,
        get_current_locale.__name__,
        get_default_locale.__name__,
        _.__name__,
        install_null_translation.__name__
]
######## export end

def init():
    from veil.component import init_component

    init_component(__name__)

init()