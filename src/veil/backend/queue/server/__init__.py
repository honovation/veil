import sandal.component

with sandal.component.init_component(__name__):
    from .job import job
    from .job import enqueue
    from .job import enqueue_at
    from .periodic_job import periodic_job
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
        queue_program.__name__,
        resweb_program.__name__,
        delayed_job_scheduler_program.__name__,
        periodic_job_scheduler_program.__name__,
        job_worker_program.__name__
    ]

    def init():
        from veil.environment.setting import register_settings_provider
        from .setting import PYRES_BASE_SETTINGS
        from .setting import ensure_veil_settings_consistent

        register_settings_provider(lambda settings: PYRES_BASE_SETTINGS, 'base')
        register_settings_provider(ensure_veil_settings_consistent, 'final')