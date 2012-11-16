from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.environment.setting import *
from veil.model.collection import *
from veil.backend.redis_setting import redis_settings
from veil.frontend.nginx_setting import nginx_server_settings
from veil.development.source_code_monitor_setting import source_code_monitor_settings
from veil.development.self_checker_setting import self_checker_settings

def init():
    register_settings_coordinator(copy_queue_settings_to_veil)
    register_settings_coordinator(add_resweb_reverse_proxy_server)
    register_settings_coordinator(copy_queue_settings_to_worker_programs)


def queue_settings(
        domain='queue.dev.dmright.com', domain_port=80,
        resweb_host=None, resweb_port=None, workers=None,
        overridden_redis_settings=None, **updates):
    updates['port'] = updates.get('port', 6389)
    settings = overridden_redis_settings or redis_settings('queue', **updates)
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
    if 'test' == VEIL_SERVER:
        del settings['resweb']
        settings.supervisor.programs.clear()
    return merge_multiple_settings(settings, source_code_monitor_settings(), self_checker_settings())


def delayed_job_scheduler_program(queue_redis_host, queue_redis_port):
    return  {
        'execute_command': 'veil sleep 3 pyres_scheduler --host={} --port={} -l info -f stderr'.format(
            queue_redis_host, queue_redis_port),
        'installer_providers': [],
        'resources': [('python_package', dict(name='pyres'))],
        'startretries': 10
    }


def periodic_job_scheduler_program():
    return {
        'execute_command': 'veil backend queue periodic-job-scheduler-up',
        'installer_providers': [],
        'resources': [('component', dict(name='veil.backend.queue'))]
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
                'type': 'immediate',
                'host': 'dummy',
                'port': 0,
                'password': 'dummy'
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


def job_worker_settings(*queue_names, **kwargs):
    if 'test' == VEIL_SERVER:
        return {}
    settings = objectify({
        'supervisor': {
            'programs': {

            }
        }
    })
    run_as = kwargs.pop('run_as', None)
    workers_count = kwargs.pop('workers_count', 1)
    worker_name = kwargs.pop('worker_name', None)
    if not worker_name:
        if len(queue_names) > 1:
            raise Exception('must give worker a name when working for more than one queue')
        worker_name = queue_names[0]
    for i in range(1, workers_count + 1):
        program_name = '{}_worker{}'.format(worker_name, i)
        settings.supervisor.programs[program_name] = worker_program(queue_names, run_as)
    return settings


def worker_program(queue_names, run_as=None):
    return {
        'execute_command': 'veil sleep 10 pyres_worker --host={{ host }} --port={{ port }} -l debug -f stderr %s'
                           % ','.join(queue_names),
        'execute_command_args': {
            #'host': will be copied by coordinator
            #'port': will be copied by coordinator
        },
        'group': 'workers',
        'user': run_as or '',
        'installer_providers': ['veil.backend.queue'],
        'resources': [('queue_worker', dict(queue_names=queue_names))],
        'startretries': 10,
        'startsecs': 10
    }

def copy_queue_settings_to_worker_programs(settings):
    if 'queue_redis' not in settings:
        return settings
    for program_name, program in settings.supervisor.programs.items():
        if 'workers' == program.get('group'):
            settings = merge_settings(settings, {
                'supervisor': {
                    'programs': {
                        program_name: {
                            'execute_command_args': {
                                'host': settings.queue_redis.bind,
                                'port': settings.queue_redis.port
                            }
                        }
                    }
                }
            })
    return settings

init()

