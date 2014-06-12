from __future__ import unicode_literals, print_function, division
import os
from veil_component import as_path
from veil.model.collection import *
from veil.profile.setting import *
from veil.frontend.nginx_setting import NGINX_PID_PATH

PERSON_WEBSITE_MAX_UPLOAD_FILE_SIZE = '3m'

PERSON_WEBSITE_BUCKETS = ['captcha_image', 'person_images']

REDIS_CLIENTS = ['persist_store', 'memory_cache']

POSTGRESQL_CLIENTS = ['vsee']

WEBSITES = ['person']

SECURITY_CONFIG_FILE = VEIL_HOME / '.config' if VEIL_ENV_TYPE in ('development', 'test') else as_path(os.getenv('HOME')) / '.config'

SECURITY_CONFIG = load_config_from(
    SECURITY_CONFIG_FILE,
    'db_user',
    'db_password',
    'db_owner',  # used for migration
    'db_owner_password',  # used for migration
    'sendgrid_username',
    'sendgrid_password',
    'hash_salt'  # used to hash password and secure cookie
)

LOGGING_LEVEL_CONFIG = objectify({
    'delayed_job_scheduler': 'info',
    'job_worker': 'info', # just control how pyres do the logging, our code still controlled by LOGGING_LEVEL_CONFIG.vsee
    'vsee_postgresql': {
        'log_min_duration_statement': 0 if VEIL_ENV_TYPE == 'development' else 300
    },
    'vsee': {
        '__default__': 'DEBUG' if VEIL_ENV_TYPE in {'development', 'test'} else 'INFO',
#        'vsee.feature': 'DEBUG',
    }
})


def env_config(person_website_start_port, person_website_process_count, person_website_domain, person_website_domain_port, persist_store_redis_host,
        persist_store_redis_port, memory_cache_redis_host, memory_cache_redis_port, vsee_postgresql_version, vsee_postgresql_host,
        vsee_postgresql_port, queue_type, queue_host, queue_port, resweb_domain, resweb_domain_port, resweb_host, resweb_port):
    return objectify(locals())


_resweb_program = resweb_program


def resweb_program(config):
    return _resweb_program(config.resweb_host, config.resweb_port, config.queue_host, config.queue_port)


def resweb_nginx_server(config):
    return nginx_server(config.resweb_domain, config.resweb_domain_port, {'/': nginx_reverse_proxy_location(config.resweb_host, config.resweb_port)})


_queue_program = queue_program


def queue_program(config):
    return _queue_program(config.queue_host, config.queue_port)


_delayed_job_scheduler_program = delayed_job_scheduler_program


def delayed_job_scheduler_program(config):
    return _delayed_job_scheduler_program(config.queue_host, config.queue_port, logging_level=LOGGING_LEVEL_CONFIG.delayed_job_scheduler)


def vsee_periodic_job_scheduler_program(config):
    return periodic_job_scheduler_program(LOGGING_LEVEL_CONFIG.vsee, application_config=vsee_config(config))

def vsee_job_worker_program(worker_name, queue_names, config, run_as=None, count=1, timeout=180):
    return job_worker_program(worker_name, LOGGING_LEVEL_CONFIG.job_worker, LOGGING_LEVEL_CONFIG.vsee, config.queue_host, config.queue_port,
        queue_names=queue_names, application_config=vsee_config(config), run_as=run_as, count=count, timeout=timeout)


def transactional_email_worker_program(config, count=1):
    return vsee_job_worker_program('transactional_email', ['send_transactional_email'], config, count=count)


def postgresql_log_rotater_program(purpose):
    return log_rotater_program('{}_postgresql'.format(purpose), '* * * * *', {
        VEIL_LOG_DIR / '{}-postgresql'.format(purpose) / '*.csv': [
            'rotate 5',
            'size=50M',
            'missingok',
            'copytruncate'
        ]
    })


def log_rotated_postgresql_program(purpose, *args, **kwargs):
    if VEIL_ENV_TYPE != 'development':
        kwargs['log_filename'] = 'postgresql.log' # will disable the builtin log rotation
    return merge_multiple_settings(postgresql_program(purpose, *args, **kwargs), postgresql_log_rotater_program(purpose))


def vsee_postgresql_program(config, more_config=None):
    more_config = more_config or {}
    return log_rotated_postgresql_program('vsee', config.vsee_postgresql_version, config.vsee_postgresql_host, config.vsee_postgresql_port,
        owner=SECURITY_CONFIG.db_owner, owner_password=SECURITY_CONFIG.db_owner_password,
        user=SECURITY_CONFIG.db_user, password=SECURITY_CONFIG.db_password,
        log_min_duration_statement=LOGGING_LEVEL_CONFIG.vsee_postgresql.log_min_duration_statement, **more_config)


def persist_store_redis_program(config):
    return redis_program('persist_store', config.persist_store_redis_host, config.persist_store_redis_port, persisted_by_aof=True)


def memory_cache_redis_program(config):
    return redis_program('memory_cache', config.memory_cache_redis_host, config.memory_cache_redis_port)


def person_website_programs(config):
    return website_programs('person', LOGGING_LEVEL_CONFIG.vsee, application_config=vsee_config(config), start_port=config.person_website_start_port,
        process_count=config.person_website_process_count)


def person_website_nginx_server(config, extra_locations=None):
    extra_locations = extra_locations or {}
    locations = website_locations('person', VEIL_ENV_TYPE in {'public', 'staging'}, max_upload_file_size=PERSON_WEBSITE_MAX_UPLOAD_FILE_SIZE)
    for purpose in PERSON_WEBSITE_BUCKETS:
        locations = merge_multiple_settings(locations, extra_locations, website_bucket_location(purpose))
    return nginx_server(config.person_website_domain, config.person_website_domain_port, locations=locations,
        upstreams=website_upstreams('person', config.person_website_start_port, config.person_website_process_count),
        error_page={'404': '404.html', '500': '500.html'}, error_page_dir='{}/static/person/error-page'.format(VEIL_HOME))


def nginx_log_rotater_program():
    return log_rotater_program('nginx', '* * * * *', {
        VEIL_LOG_DIR / 'nginx' / '*.log': [
            'rotate 5',
            'size=50M',
            'missingok',
            'notifempty',
            'sharedscripts',
            'postrotate',
            'if [ -f {} ]; then'.format(NGINX_PID_PATH),
            'kill -USR1 `cat {}`'.format(NGINX_PID_PATH),
            'fi',
            'endscript'
        ]
    })


def log_rotated_nginx_program(*args, **kwargs):
    return merge_multiple_settings(nginx_program(*args, **kwargs), nginx_log_rotater_program())


def vsee_config(config):
    vsee_config_ = objectify({
        'queue_client': {
            'type': config.queue_type,
            'host': config.queue_host,
            'port': config.queue_port
        },
        'sendgrid_client': {
            'username': SECURITY_CONFIG.sendgrid_username,
            'password': SECURITY_CONFIG.sendgrid_password
        },
        'hash': {
            'salt': SECURITY_CONFIG.hash_salt
        }
    })
    for purpose in REDIS_CLIENTS:
        vsee_config_['{}_redis_client'.format(purpose)] = {
            'host': config['{}_redis_host'.format(purpose)],
            'port': config['{}_redis_port'.format(purpose)]
        }
    person_website_authority = config.person_website_domain if 80 == config.person_website_domain_port else '{}:{}'.format(
        config.person_website_domain, config.person_website_domain_port)
    for purpose in PERSON_WEBSITE_BUCKETS:
        vsee_config_['{}_bucket'.format(purpose)] = {
            'type': 'filesystem',
            'base_directory': VEIL_BUCKETS_DIR / purpose.replace('_', '-'),
            'base_url': 'http://{}/{}'.format(person_website_authority, purpose.replace('_', '-')),
        }
    for purpose in POSTGRESQL_CLIENTS:
        vsee_config_['{}_database_client'.format(purpose)] = {
            'driver': 'veil.backend.database.postgresql',
            'type': 'postgresql',
            'host': config['{}_postgresql_host'.format(purpose)],
            'port': config['{}_postgresql_port'.format(purpose)],
            'database': purpose,
            'user': SECURITY_CONFIG.db_user,
            'password': SECURITY_CONFIG.db_password,
            'schema': 'public'
        }
    for purpose in WEBSITES:
        vsee_config_['{}_website'.format(purpose)] = {
            'domain': config['{}_website_domain'.format(purpose)],
            'domain_port': config['{}_website_domain_port'.format(purpose)],
            'start_port': config['{}_website_start_port'.format(purpose)],
            'locale': 'zh_Hans_CN.UTF-8',
            'master_template_directory': VEIL_HOME / 'src' / 'vsee' / 'website' / purpose,
            'prevents_xsrf': True,
            'recalculates_static_file_hash': True,
            'clears_template_cache': True
        }
    return vsee_config_


def website_bucket_location(purpose):
    bucket_base_directory = VEIL_BUCKETS_DIR / purpose.replace('_', '-')
    return {'^~ /{}/'.format(purpose.replace('_', '-')): bucket_location(bucket_base_directory)}
