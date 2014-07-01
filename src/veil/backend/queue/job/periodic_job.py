from __future__ import unicode_literals, print_function, division
from datetime import timedelta
from collections import defaultdict
from croniter.croniter import croniter
from veil_component import *
from veil.utility.clock import get_current_timestamp
from .job import JobHandlerDecorator

schedules = defaultdict(set)  # schedule => set(job_handler)


def get_periodic_job_schedules():
    return schedules


def periodic_job(schedule, queue=None):
    if isinstance(schedule, timedelta):
        return PeriodicJobHandlerDecorator(TimedeltaSchedule(schedule), queue)
    else:
        return PeriodicJobHandlerDecorator(CroniterSchedule(schedule), queue)


class PeriodicJobHandlerDecorator(object):
    def __init__(self, schedule, queue):
        self.schedule = schedule
        self.queue = queue

    def __call__(self, job_handler):
        job_handler = JobHandlerDecorator(self.queue)(job_handler)
        record_dynamic_dependency_provider(get_loading_component_name(), 'periodic-job', '@')
        schedules[self.schedule].add(job_handler)
        return job_handler


class TimedeltaSchedule(object):
    def __init__(self, timedelta):
        self.seconds = timedelta.total_seconds()
        if self.seconds < 1:
            raise Exception('timedelta must be greater than or equal with one second')
        self.timedelta = timedelta

    def get_next_timestamp(self, now=None):
        now = now or get_current_timestamp()
        return now + self.seconds

    def __repr__(self):
        return str(self.timedelta)


class CroniterSchedule(object):
    def __init__(self, crontab_expression):
        croniter(crontab_expression) # validate the expression, throws exception if invalid
        self.crontab_expression = crontab_expression

    def get_next_timestamp(self, now=None):
        now = now or get_current_timestamp()
        return croniter(self.crontab_expression, now).get_next(ret_type=float)

    def __repr__(self):
        return self.crontab_expression
