# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import random
import logging
from veil.backend.queue import *
from veil.backend.redis import *
from veil.environment import get_application_sms_whitelist
from veil_component import VEIL_ENV_TYPE

LOGGER = logging.getLogger(__name__)

queue = register_queue()
redis = register_redis('persist_store')

_sms_providers = {}
current_sms_provider = None
SENT_SMS_RECORD_ALIVE_IN_SECONDS = 60 * 60


def sent_sms_redis_key(mobile, sms_code):
    return '{}:{}'.format(mobile, sms_code)


def register_sms_provider(sms_provider):
    if sms_provider.sms_provider_id not in _sms_providers:
        _sms_providers[sms_provider.sms_provider_id] = sms_provider
        global current_sms_provider
        if not current_sms_provider:
            current_sms_provider = sms_provider


def list_sms_providers():
    print(_sms_providers)


def set_current_sms_provider():
    if not len(_sms_providers):
        raise Exception('no sms providers')
    global current_sms_provider
    if not current_sms_provider:
        current_sms_provider = random.choice(_sms_providers.values())


def shuffle_current_sms_provider(excluded_provider_ids):
    sms_provider_candidates = [sp for sp in _sms_providers.values() if sp.sms_provider_id not in excluded_provider_ids]
    if not sms_provider_candidates:
        return
    global current_sms_provider
    current_sms_provider = random.choice(sms_provider_candidates)


@job('send_transactional_sms', retry_every=10, retry_timeout=90)
def send_transactional_sms_job(receivers, message, sms_code, last_sms_code=None):
    global current_sms_provider
    receiver_list = current_sms_provider.get_receiver_list(receivers)
    if len(receiver_list) == 1:
        receivers = receiver_list[0]
        send_sms(receivers, message, sms_code, last_sms_code=last_sms_code)
    else:
        for receivers_ in receiver_list:
            queue().enqueue(send_transactional_sms_job, receivers=receivers_, message=message, sms_code=sms_code, last_sms_code=last_sms_code)
        return
    with redis().pipeline() as pipe:
        for receiver in receivers:
            pipe.setex(sent_sms_redis_key(receiver, sms_code), SENT_SMS_RECORD_ALIVE_IN_SECONDS, current_sms_provider.sms_provider_id)
        pipe.execute()


@job('send_slow_transactional_sms', retry_every=10 * 60, retry_timeout=3 * 60 * 60)
def send_slow_transactional_sms_job(receivers, message, sms_code):
    global current_sms_provider
    receiver_list = current_sms_provider.get_receiver_list(receivers)
    if len(receiver_list) == 1:
        receivers = receiver_list[0]
        send_sms(receivers, message, sms_code)
    else:
        for receivers_ in receiver_list:
            queue().enqueue(send_slow_transactional_sms_job, receivers=receivers_, message=message, sms_code=sms_code)


@job('send_marketing_sms', retry_every=10 * 60, retry_timeout=3 * 60 * 60)
def send_marketing_sms_job(receivers, message, sms_code):
    global current_sms_provider
    receiver_list = current_sms_provider.get_receiver_list(receivers)
    if len(receiver_list) == 1:
        receivers = receiver_list[0]
        send_sms(receivers, message, sms_code, transactional=False)
    else:
        for receivers_ in receiver_list:
            queue().enqueue(send_marketing_sms_job, receivers=receivers_, message=message, sms_code=sms_code)


def send_sms(receivers, message, sms_code, last_sms_code=None, transactional=True):
    used_sms_provider_ids = set()
    if last_sms_code:
        last_sms_provider_id = redis().get(sent_sms_redis_key(receivers[0], last_sms_code))
        if last_sms_provider_id:
            used_sms_provider_ids.add(int(last_sms_provider_id))
            shuffle_current_sms_provider(used_sms_provider_ids)
    if 'public' != VEIL_ENV_TYPE:
        receivers_not_in_whitelist = set(r for r in receivers if r not in get_application_sms_whitelist())
        if receivers_not_in_whitelist:
            LOGGER.warn('Ignored sms receivers not in the whitelist under non-public env: %(receivers_not_in_whitelist)s', {
                'receivers_not_in_whitelist': receivers_not_in_whitelist
            })
            receivers -= receivers_not_in_whitelist
            if not receivers:
                return
    while True:
        try:
            current_sms_provider.send(receivers, message, sms_code, transactional)
        except SendError as e:
            LOGGER.error(e.message)
            used_sms_provider_ids.add(current_sms_provider.sms_provider_id)
            shuffle_current_sms_provider(used_sms_provider_ids)
            if current_sms_provider.sms_provider_id in used_sms_provider_ids:
                raise Exception('not enough reliable sms providers')
        else:
            break


class SMService(object):
    def __init__(self, sms_provider_id):
        self._sms_provider_id = sms_provider_id

    @property
    def sms_provider_id(self):
        return self._sms_provider_id

    def get_receiver_list(self, receivers):
        raise NotImplementedError()

    def send(self, receivers, message, sms_code, transactional):
        raise NotImplementedError()

    def query_balance(self):
        raise NotImplementedError()


class SendError(Exception):
    pass
