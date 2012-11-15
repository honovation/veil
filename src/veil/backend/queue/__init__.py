import veil_component

with veil_component.init_component(__name__):
    from .job import job
    from .periodic_job import periodic_job
    from .queue import require_queue

    __all__ = [
        job.__name__,
        periodic_job.__name__,
        require_queue.__name__,
    ]

    def init():
        from veil.development.source_code_monitor import register_reloads_on_change_group

        register_reloads_on_change_group('workers')
