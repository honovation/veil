from veil_installer import *

import veil_component
with veil_component.init_component(__name__):

    from .job_queue import task
    from .job_queue import periodic
    from .job_queue import cron_expr
    from .job_queue import fixed
    from .job_queue import linear
    from .job_queue import exponential
    from .job_queue import count_failed_jobs
    from .retry import discrete
    from .queue_client_installer import queue_client_resource
    from .tasktiger_admin_installer import tasktiger_admin_resource

    def init():
        add_application_sub_resource('queue_client', lambda config: queue_client_resource(**config))

    __all__ = [
        task.__name__,
        periodic.__name__,
        cron_expr.__name__,
        fixed.__name__,
        linear.__name__,
        exponential.__name__,
        count_failed_jobs.__name__,

        discrete.__name__,

        queue_client_resource.__name__,

        tasktiger_admin_resource.__name__,
    ]
