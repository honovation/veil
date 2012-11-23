import veil_component

with veil_component.init_component(__name__):
    from veil_installer import *
    from veil.environment import *
    from veil.environment.setting import *
    from veil.backend.database.postgresql_setting import postgresql_program
    from veil.backend.database.database_client_setting import database_client_resource
    from veil.backend.redis_setting import redis_program
    from veil.backend.redis_setting import redis_client_resource
    from veil.backend.queue_setting import queue_program
    from veil.backend.queue_setting import resweb_program
    from veil.backend.queue_setting import delayed_job_scheduler_program
    from veil.backend.queue_setting import periodic_job_scheduler_program
    from veil.backend.queue_setting import job_worker_program
    from veil.backend.queue_setting import queue_client_resource
    from veil.backend.bucket_setting import bucket_resource
    from veil.backend.bucket_setting import bucket_location
    from veil.backend.web_service_setting import web_service_client_resource
    from veil.frontend.nginx_setting import nginx_program
    from veil.frontend.nginx_setting import nginx_server
    from veil.frontend.nginx_setting import nginx_reverse_proxy_location
    from veil.frontend.website_setting import website_program
    from veil.frontend.website_setting import website_locations
    from veil.frontend.website_setting import website_resource
    from veil.frontend.captcha_setting import captcha_resources
    from veil.development.source_code_monitor_setting import source_code_monitor_program
