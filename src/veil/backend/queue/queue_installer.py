from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.environment.setting import *
from veil.environment.installation import *
from veil.frontend.template import *

@installation_script()
def install_queue_api():
    install_python_package('pytz')
    install_python_package('pyres')
    install_python_package('croniter')


@script('install-resweb')
def install_queue_server():
    settings = get_settings()
    install_queue_api()
    install_python_package('resweb')
    create_file(settings.resweb.config_file, content=get_template('resweb.cfg.j2').render(
        queue_config=settings.queue_redis,
        config=settings.resweb))


@script('install-delayed-job-scheduler')
def install_delayed_job_scheduler():
    install_queue_api()


@script('install-periodic-job-scheduler')
def install_delayed_job_scheduler():
    install_queue_api()


@script('install-worker')
def install_worker(queue_name):
    install_queue_api()
    # TODO: install the components where job handlers resides in