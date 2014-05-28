from __future__ import unicode_literals, print_function, division
from veil.profile.setting import *
import __env__

DEVELOPMENT_SUPERVISOR_HTTP_PORT = 9090
DEVELOPMENT_REDIS_HOST = '127.0.0.1'
DEVELOPMENT_REDIS_PORT = 6379

config = __env__.env_config(
    person_website_start_port=2000,
    person_website_processes_count=1,
    person_website_domain='person.dev.dmright.com',
    person_website_domain_port=80,
    persist_store_redis_host=DEVELOPMENT_REDIS_HOST,
    persist_store_redis_port=DEVELOPMENT_REDIS_PORT,
    memory_cache_redis_host=DEVELOPMENT_REDIS_HOST,
    memory_cache_redis_port=DEVELOPMENT_REDIS_PORT,
    vsee_postgresql_version='9.3',
    vsee_postgresql_host='127.0.0.1',
    vsee_postgresql_port=5432,
    queue_type='redis',
    queue_host=DEVELOPMENT_REDIS_HOST,
    queue_port=DEVELOPMENT_REDIS_PORT,
    resweb_domain='queue.dev.dmright.com',
    resweb_domain_port=80,
    resweb_host='127.0.0.1',
    resweb_port=7070)

ENV_DEVELOPMENT = {
    'development': veil_env(hosts={}, servers={
        '@': veil_server(
            host_name='',
            sequence_no=10,
            supervisor_http_port=DEVELOPMENT_SUPERVISOR_HTTP_PORT,
            programs=merge_multiple_settings(
                redis_program('development', DEVELOPMENT_REDIS_HOST, DEVELOPMENT_REDIS_PORT),
                __env__.vsee_postgresql_program(config),
                __env__.resweb_program(config),
                __env__.delayed_job_scheduler_program(config),
                __env__.vsee_periodic_job_scheduler_program(config),
                __env__.vsee_job_worker_program(
                    worker_name='development',
                    queue_names=[
                        'send_transactional_email',
                    ],
                    config=config, count=2),
                __env__.person_website_programs(config),
                __env__.log_rotated_nginx_program(merge_multiple_settings(
                    __env__.resweb_nginx_server(config),
                    __env__.person_website_nginx_server(config),
                ))
            )
        )
    })
}
