import veil_component

with veil_component.init_component(__name__):
    from .job import job
    from .job import periodic_job
    from .job import IgnorableInvalidJob

    from .queue import register_queue

    from .queue_maintenance import count_failed_jobs
    from .queue_maintenance import delete_pending_jobs
    from .queue_maintenance import delete_failed_jobs

    from .queue_client_installer import queue_client_resource

    from .resweb_installer import resweb_resource

    from tasktiger import TaskTiger

    from .tasktiger_admin_installer import tasktiger_admin_resource

    __all__ = [
        job.__name__,
        periodic_job.__name__,
        IgnorableInvalidJob.__name__,

        register_queue.__name__,

        count_failed_jobs.__name__,
        delete_pending_jobs.__name__,
        delete_failed_jobs.__name__,

        queue_client_resource.__name__,

        resweb_resource.__name__,

        TaskTiger.__name__,

        tasktiger_admin_resource.__name__,
    ]
