import sandal.component

with sandal.component.init_component(__name__):
    from .job import job
    from .job import enqueue
    from .job import enqueue_at
    from .periodic_job import periodic_job
    from .setting import pyres_settings
    from .setting import queue_program
    from .setting import resweb_program
    from .setting import delayed_job_scheduler_program
    from .setting import periodic_job_scheduler_program
    from .setting import job_worker_program

    __all__ = [
        # from job
        job.__name__,
        enqueue.__name__,
        enqueue_at.__name__,
        # from periodic_job
        periodic_job.__name__,
        # from setting
        pyres_settings.__name__,
        queue_program.__name__,
        resweb_program.__name__,
        delayed_job_scheduler_program.__name__,
        periodic_job_scheduler_program.__name__,
        job_worker_program.__name__
    ]

    def init():
        from veil.environment.setting import register_settings_coordinator
        from .setting import copy_queue_settings_to_veil

        register_settings_coordinator(copy_queue_settings_to_veil)