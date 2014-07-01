# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from logging import getLogger
import time
from pyres import ResQ

LOGGER = getLogger(__name__)


class ResQWrapper(ResQ):
    def __init__(self, server, password=None):
        super(ResQWrapper, self).__init__(server, password)

    def enqueue_at_from_string(self, datetime, klass_as_string, queue, *args, **kwargs):
        LOGGER.info('scheduled %(klass_as_string)s job on queue %(queue)s for execution at %(datetime)s', {
            'klass_as_string': klass_as_string, 'queue': queue, 'datetime': datetime
        })
        if args:
            LOGGER.debug('job arguments are: %(args)s', {'args': args})
        payload = {'class': klass_as_string, 'queue': queue, 'args': args}
        if 'first_attempt' in kwargs:
            payload['first_attempt'] = kwargs['first_attempt']
        self.delayed_push(datetime, payload)

    def enqueue_from_string(self, klass_as_string, queue, *args, **kwargs):
        payload = {'class': klass_as_string, 'args': args, 'enqueue_timestamp': time.time()}
        if 'first_attempt' in kwargs:
            payload['first_attempt'] = kwargs['first_attempt']
        self.push(queue, payload)
        LOGGER.info('enqueued %(klass_as_string)s job on queue %(queue)s', {'klass_as_string': klass_as_string, 'queue': queue})
        if args:
            LOGGER.debug('job arguments: %(args)s', {'args': args})
        else:
            LOGGER.debug('no arguments passed in.')
