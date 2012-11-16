import veil_component

with veil_component.init_component(__name__):
    from veil.environment import *
    from veil.environment.setting import *
    from veil.environment.supervisor_setting import supervisor_settings
    from veil.backend.database.postgresql_setting import postgresql_settings
    from veil.backend.bucket_setting import bucket_settings
    from veil.backend.database.db2_setting import db2_settings
    from veil.frontend.website_setting import website_settings
    from veil.frontend.captcha_setting import captcha_settings
    from veil.backend.queue_setting import queue_settings
    from veil.backend.queue_setting import job_worker_settings
    from veil.backend.queue_setting import periodic_job_scheduler_settings
    from veil.backend.redis_setting import redis_settings
    from veil.backend.web_service_setting import web_service_settings
