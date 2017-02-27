# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import os
import time
from optparse import OptionParser
from pyres import setup_pidfile, special_log_file
import pyres.horde
from pyres.horde import setproctitle

from veil.frontend.cli import *
from veil.model.event import *
from veil.server.process import *
from veil_component import VEIL_ENV
from veil.backend.redis import *

redis = register_redis('persist_store')


@script('pyres_manager')
def pyres_manager_bootstrap_script(*args):
    usage = "usage: %prog [options] arg1"
    parser = OptionParser(usage=usage)
    #parser.add_option("-q", dest="queue_list")
    parser.add_option("--host", dest="host", default="localhost")
    parser.add_option("--port", dest="port", type="int", default=6379)
    parser.add_option("--password", dest="password", default=None)
    parser.add_option("-i", '--interval', dest='manager_interval', default=2, help='the default time interval to sleep between runs - manager')
    parser.add_option("--minions_interval", dest='minions_interval', default=5, help='the default time interval to sleep between runs - minions')
    parser.add_option('-l', '--log-level', dest='log_level', default='info', help='log level.  Valid values are "debug", "info", "warning", "error", "critical", in decreasing order of verbosity. Defaults to "info" if parameter not specified.')
    parser.add_option("--pool", type="int", dest="pool_size", default=1, help="Number of minions to spawn under the manager.")
    parser.add_option("-j", "--process_max_jobs", dest="max_jobs", type=int, default=0, help='how many jobs should be processed on worker run.')
    parser.add_option('-f', dest='logfile', help='If present, a logfile will be used.  "stderr", "stdout", and "syslog" are all special values.')
    parser.add_option('-p', dest='pidfile', help='If present, a pidfile will be used.')
    parser.add_option("--concat_minions_logs", action="store_true", dest="concat_minions_logs", help='Concat all minions logs on same file.')
    (options, args) = parser.parse_args(args=list(args))

    if len(args) != 1:
        parser.print_help()
        parser.error("Argument must be a comma seperated list of queues")

    log_level = getattr(logging, options.log_level.upper(), 'INFO')
    #logging.basicConfig(level=log_level, format="%(asctime)s: %(levelname)s: %(message)s")
    concat_minions_logs = options.concat_minions_logs
    setup_pidfile(options.pidfile)

    manager_interval = options.manager_interval
    if manager_interval is not None:
        manager_interval = float(manager_interval)

    minions_interval = options.minions_interval
    if minions_interval is not None:
        minions_interval = float(minions_interval)

    queues = args[0].split(',')
    server = '%s:%s' % (options.host, options.port)
    password = options.password
    Manager.run(pool_size=options.pool_size, queues=queues, server=server, password=password, interval=manager_interval, logging_level=log_level,
                log_file=options.logfile, minions_interval=minions_interval, concat_minions_logs=concat_minions_logs, max_jobs=options.max_jobs)


class Manager(pyres.horde.Khan):
    def _add_minion(self):
        if hasattr(self, 'logger'):
            self.logger.info('Adding minion')
        if self.log_file:
            if special_log_file(self.log_file):
                log_path = self.log_file
            else:
                log_path = os.path.dirname(self.log_file)
        else:
            log_path = None
        m = Minion(self.queues, self.server, self.password, interval=self.minions_interval,
                   log_level=self.logging_level, log_path=log_path, concat_logs=self.concat_minions_logs,
                   max_jobs=self.max_jobs)
        m.start()
        self._workers[m.pid] = m
        if hasattr(self, 'logger'):
            self.logger.info('minion added at: %s' % m.pid)
        return m

    def _remove_minion(self, pid=None):
        if pid:
            m = self._workers.pop(pid)
        else:
            pid, m = self._workers.popitem(False)
        m.terminate()
        self.resq.redis.srem('resque:khans', str(self))
        self.pool_size -= 1
        self.resq.redis.sadd('resque:khans', str(self))
        return m

    def check_children(self):
        need_restart_minion_pids = self.resq.redis.smembers('resque:khan:{}:restart-minion-pids'.format(self.pid))
        self.logger.debug('need restart minion pids: %s' % need_restart_minion_pids)
        if need_restart_minion_pids:
            for pid in need_restart_minion_pids:
                self.logger.debug('find need restart minion: %s' % pid)
                self._remove_minion(int(pid))
                self._add_minion()
            self.resq.redis.delete('resque:khan:{}:restart-minion-pids'.format(self.pid))

    def _check_commands(self):
        super(Manager, self)._check_commands()
        self.check_children()


class Minion(pyres.horde.Minion):
    def startup(self):
        super(Minion, self).startup()
        # load_all_components()

    def working_on(self, job):
        super(Minion, self).working_on(job)
        publish_event(EVENT_PROCESS_SETUP)

    def unregister_minion(self):
        super(Minion, self).unregister_minion()
        self.resq.redis.sadd('resque:khan:{}:restart-minion-pids'.format(self._parent_pid), self.pid)

    def work(self, interval=5):
        self.startup()
        cur_job = 0
        while True:
            setproctitle('pyres_minion:%s: waiting for job on: %s' % (os.getppid(), self.queues))
            self.logger.info('waiting on job')
            if self._shutdown:
                self.logger.info('shutdown scheduled')
                break
            self.logger.debug('max_jobs: %d cur_jobs: %d' % (self.max_jobs, cur_job))
            if 0 < self.max_jobs <= cur_job:
                self.logger.debug('max_jobs reached on %s: %d' % (self.pid, cur_job))
                self.logger.debug('minion will shutdown')
                self.schedule_shutdown(None, None)
            job = self.reserve()
            if job:
                self.process(job)
                cur_job += 1
            else:
                self.logger.debug('minion sleeping for: %d secs' % interval)
                time.sleep(interval)
        self.unregister_minion()

    def done_working(self):
        try:
            publish_event(EVENT_PROCESS_TEARDOWN, loads_event_handlers=False)
        except Exception:
            self.logger.warn('exception thrown while publishing EVENT_PROCESS_TEARDOWN', exc_info=1)
        super(Minion, self).done_working()

    def reserve(self):
        if VEIL_ENV.is_prod and 'true' != redis().get('reserve_job'):
            return None
        return super(Minion, self).reserve()
