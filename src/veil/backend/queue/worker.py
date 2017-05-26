# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from optparse import OptionParser
import logging
import pyres.worker
import redis
from pyres import setup_logging, setup_pidfile
from veil.frontend.cli import *
from veil.model.event import *
from veil.server.process import *
from .queue import is_jobs_given_up
from tasktiger import TaskTiger


@script('pyres_worker')
def pyres_worker_bootstrap_script(*args):
    # copied from pyres.scripts
    usage = "usage: %prog [options] arg1"
    parser = OptionParser(usage=usage)

    parser.add_option("--host", dest="host", default="localhost")
    parser.add_option("--port", dest="port", type="int", default=6379)
    parser.add_option("--password", dest="password", default=None)
    parser.add_option("-i", '--interval', dest='interval', default=None, help='the default time interval to sleep between runs')
    parser.add_option('-l', '--log-level', dest='log_level', default='info', help='log level.  Valid values are "debug", "info", "warning", "error", "critical", in decreasing order of verbosity. Defaults to "info" if parameter not specified.')
    parser.add_option('-f', dest='logfile', help='If present, a logfile will be used.  "stderr", "stdout", and "syslog" are all special values.')
    parser.add_option('-p', dest='pidfile', help='If present, a pidfile will be used.')
    parser.add_option("-t", '--timeout', dest='timeout', default=None, help='the timeout in seconds for this worker')
    (options, args) = parser.parse_args(args=list(args))

    if len(args) != 1:
        parser.print_help()
        parser.error("Argument must be a comma seperated list of queues")

    log_level = getattr(logging, options.log_level.upper(), 'INFO')
    setup_logging(procname="pyres_worker", log_level=log_level, filename=options.logfile)
    setup_pidfile(options.pidfile)

    interval = options.interval
    if interval is not None:
        interval = int(interval)

    timeout = options.timeout and int(options.timeout)

    queues = args[0].split(',')
    server = '%s:%s' % (options.host, options.port)
    password = options.password
    Worker.run(queues, server, password, interval, timeout=timeout)


class Worker(pyres.worker.Worker):
    def before_process(self, job):
        publish_event(EVENT_PROCESS_SETUP)
        return super(Worker, self).before_process(job)

    def done_working(self, job):
        try:
            publish_event(EVENT_PROCESS_TEARDOWN, loads_event_handlers=False)
        except Exception:
            self.logger.warn('exception thrown while publishing EVENT_PROCESS_TEARDOWN', exc_info=1)
        super(Worker, self).done_working(job)

    def reserve(self, timeout=10):
        if is_jobs_given_up(self.resq.redis):
            return None
        return super(Worker, self).reserve(timeout=timeout)
