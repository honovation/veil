######## export begin
from .template import template_filter
from .template import register_template_filter
from .template import template_utility
from .template import register_template_utility
from .template import register_template_loader
from .template import require_current_translations_being
from .template import require_current_template_directory_being
from .template import require_current_template_directory_relative_to
from .template import get_template
from .template import get_template_environment
from .template import reset_template_environment
from .template import register_template_post_processor
from .widget import widget
from .widget import page
from .widget import register_page_post_processor

__all__ = [
        # from template
        template_filter.__name__,
        register_template_filter.__name__,
        template_utility.__name__,
        register_template_utility.__name__,
        register_template_loader.__name__,
        require_current_translations_being.__name__,
        require_current_template_directory_being.__name__,
        require_current_template_directory_relative_to.__name__,
        get_template.__name__,
        get_template_environment.__name__,
        register_template_post_processor.__name__,
        # from widget
        widget.__name__,
        page.__name__,
        reset_template_environment.__name__,
        register_page_post_processor.__name__
]
######## export end

def init():
    from sandal.component import init_component
    from sandal.event import subscribe_event
    from sandal.const import consts
    from .widget import on_template_environment_ready
    from .widget import on_template_environment_reset

    init_component(__name__)
    subscribe_event(consts.EVENT_TEMPLATE_ENVIRONMENT_READY, on_template_environment_ready)
    subscribe_event(consts.EVENT_TEMPLATE_ENVIRONMENT_RESET, on_template_environment_reset)

init()