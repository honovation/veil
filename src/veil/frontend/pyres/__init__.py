######## export begin
from .job import job
from .job import enqueue
from .job import enqueue_at
from .periodic_job import periodic_job
from .setting import PYRES_BASE_SETTINGS

__all__ = [
    # from job
    job.__name__,
    enqueue.__name__,
    enqueue_at.__name__,
    # from periodic_job
    periodic_job.__name__
]
######## export end

def init():
    from veil.component import init_component
    from veil.environment.deployment import register_deployment_settings_provider

    init_component(__name__)
    register_deployment_settings_provider(lambda: PYRES_BASE_SETTINGS)

init()