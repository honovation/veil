import veil_component

with veil_component.init_component(__name__):
    from .job import job
    from .periodic_job import periodic_job
    from .queue import require_queue
    from .queue_setting import queue_settings

    __all__ = [
        job.__name__,
        periodic_job.__name__,
        require_queue.__name__,
        queue_settings.__name__
    ]

    def init():
        from veil.environment.setting import register_settings_coordinator
        from .queue_setting import copy_queue_settings_to_veil
        from .queue_setting import add_resweb_reverse_proxy_server

        register_settings_coordinator(copy_queue_settings_to_veil)
        register_settings_coordinator(add_resweb_reverse_proxy_server)
