import veil_component

with veil_component.init_component(__name__):
    from veil_installer import *
    from veil.environment import *
    from veil.environment.setting import *
    from veil.backend.database.postgresql_setting import postgresql_program
    from veil.backend.redis_setting import redis_program
    from veil.backend.queue_setting import queue_program
    from veil.backend.queue_setting import resweb_program
    from veil.backend.queue_setting import delayed_job_scheduler_program
    from veil.backend.queue_setting import periodic_job_scheduler_program
    from veil.backend.queue_setting import job_worker_program
    from veil.backend.bucket_setting import bucket_location
    from veil.frontend.nginx_setting import nginx_program
    from veil.frontend.nginx_setting import nginx_server
    from veil.frontend.nginx_setting import nginx_reverse_proxy_location
    from veil.frontend.website_setting import website_programs
    from veil.frontend.website_setting import website_locations
    from veil.frontend.website_setting import website_upstreams
    from veil.development.source_code_monitor_setting import source_code_monitor_program
