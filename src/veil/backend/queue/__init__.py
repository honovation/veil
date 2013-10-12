import veil_component

with veil_component.init_component(__name__):
    from .job import job
    from .job import InvalidJob
    from .periodic_job import periodic_job
    from .queue import register_queue
    from .queue_maintenance import delete_pending_jobs
    from .queue_maintenance import delete_failed_jobs
    from .server.resweb_installer import resweb_resource
    from .queue_client_installer import queue_client_resource

    __all__ = [
        job.__name__,
        InvalidJob.__name__,
        periodic_job.__name__,
        register_queue.__name__,
        delete_pending_jobs.__name__,
        delete_failed_jobs.__name__,
        resweb_resource.__name__,
        queue_client_resource.__name__
    ]