from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.backend.redis import *
from veil.frontend.nginx import *
from .server.delayed_job_scheduler_program import delayed_job_scheduler_program
from .server.periodic_job_scheduler_program import periodic_job_scheduler_program
from .server.worker_program import worker_program
from .server.resweb_program import resweb_program

def queue_settings(
        domain='queue.dev.dmright.com', domain_port=80,
        resweb_host=None, resweb_port=None, workers=None, **updates):
    updates['port'] = updates.get('port', 6389)
    settings = redis_settings('queue', **updates)
    queue_redis_host = settings.queue_redis.bind()
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
        for i in range(1, workers_count + 1):
            settings.supervisor.programs['{}_worker{}'.format(queue_name, i)] = worker_program(
                queue_redis_host, queue_redis_port, queue_name)
    if 'test' == VEIL_ENV:
        settings.supervisor.programs.clear()
    return settings


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





