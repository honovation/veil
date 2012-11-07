from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.backend.redis_setting import redis_settings
from veil.frontend.nginx_setting import nginx_server_settings

def init():
    register_settings_coordinator(copy_queue_settings_to_veil)
    register_settings_coordinator(add_resweb_reverse_proxy_server)


def queue_settings(
        domain='queue.dev.dmright.com', domain_port=80,
        resweb_host=None, resweb_port=None, workers=None, **updates):
    updates['port'] = updates.get('port', 6389)
    settings = redis_settings('queue', **updates)
    queue_redis_host = settings.queue_redis.bind
    queue_redis_port = settings.queue_redis.port
    settings = merge_settings(settings, {
        'resweb': {
            'config_file': VEIL_ETC_DIR / 'resweb.cfg',
            'server_host': resweb_host or 'localhost',
            'server_port': resweb_port or 7070,
            'domain': domain,
            'domain_port': domain_port
        }
    })
    settings = merge_settings(settings, {
        'supervisor': {
            'programs': {
                'resweb': resweb_program(),
                'delayed_job_scheduler': delayed_job_scheduler_program(queue_redis_host, queue_redis_port),
                'periodic_job_scheduler': periodic_job_scheduler_program()
            }
        }
    })
    workers = workers or None
    for queue_name, workers_count in workers.items():
        if isinstance(workers_count, (list, tuple)):
            workers_user = workers_count[0]
            workers_count = workers_count[1]
            for i in range(1, workers_count + 1):
                settings.supervisor.programs['{}_worker{}'.format(queue_name, i)] = worker_program(
                    queue_redis_host, queue_redis_port, queue_name, user=workers_user)
        else:
            for i in range(1, workers_count + 1):
                settings.supervisor.programs['{}_worker{}'.format(queue_name, i)] = worker_program(
                    queue_redis_host, queue_redis_port, queue_name)
    if 'test' == VEIL_ENV:
        del settings['resweb']
        settings.supervisor.programs.clear()
    return settings


def delayed_job_scheduler_program(queue_redis_host, queue_redis_port):
    return  {
        'execute_command': 'pyres_scheduler --host={} --port={} -l info -f stderr'.format(
            queue_redis_host, queue_redis_port),
        'installer_providers': [],
        'resources': [('python_package', dict(name='pyres'))]
    }


def periodic_job_scheduler_program():
    return {
        'execute_command': 'veil backend queue periodic-job-scheduler-up',
        'installer_providers': [],
        'resources': [('component', 'veil.backend.queue')]
    }


def worker_program(queue_redis_host, queue_redis_port, queue_name, user=None):
    return {
        'execute_command': 'pyres_worker --host={} --port={} -l debug -f stderr {}'.format(
            queue_redis_host, queue_redis_port, queue_name),
        'group': '{}_workers'.format(queue_name),
        'user': '{}'.format(user) if user else '',
        'installer_providers': ['veil.backend.queue'],
        'resources': [('queue_worker', dict(name=queue_name))]
    }


def resweb_program():
    return {
        'execute_command': 'resweb',
        'environment_variables': {'RESWEB_SETTINGS': VEIL_ETC_DIR / 'resweb.cfg'},
        'installer_providers': ['veil.backend.queue'],
        'resources': [('resweb', {})]
    }


def copy_queue_settings_to_veil(settings):
    if 'queue_redis' not in settings:
        return settings
    return merge_settings(settings, {
        'veil': {
            'queue': {
                'type': 'redis',
                'host': settings.queue_redis.bind,
                'port': settings.queue_redis.port,
                'password': settings.queue_redis.password
            } if 'test' != VEIL_ENV else {
                'type': 'immediate'
            }
        }
    }, overrides=True)


def add_resweb_reverse_proxy_server(settings):
    if not settings.get('resweb'):
        return settings
    server_name = settings.resweb.domain
    return merge_settings(settings, nginx_server_settings(settings, server_name,
        listen=settings.resweb.domain_port,
        locations={
            '/': {
                '_': """
                        proxy_pass http://%s:%s;
                        proxy_set_header   Host             $host;
                        proxy_set_header   X-Real-IP        $remote_addr;
                        proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
                        """ % (
                    settings.resweb.server_host,
                    settings.resweb.server_port),
            },
        }
    ))

init()

