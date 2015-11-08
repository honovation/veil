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
SMS_PROVIDER_BALANCE_THRESHOLD = 2000
SMS_PROVIDER_BALANCE_ALIVE_IN_SECONDS = 60 * 60 * 36
SMS_PROVIDER_SENT_QUANTITY_ALIVE_IN_SECONDS = 60 * 60 * 36


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


@periodic_job('31 6 * * *')
def check_sms_provider_balance_and_reconciliation_job():
    error_messages = []
    for instance in _sms_providers.values():
        error_messages.extend(instance.check_balance_and_reconciliation())
    if error_messages:
        raise Exception(', '.join(error_messages))


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
            current_sms_provider.add_sent_quantity(current_sms_provider.get_minimal_message_quantity(message) * len(receivers))
            break


class SMService(object):
    def __init__(self, sms_provider_id):
        self._sms_provider_id = sms_provider_id
        self.balance_key_in_redis = '{}:{}:{}:balance'.format('VEIL', 'SMS', sms_provider_id)
        self.sent_quantity_key_in_redis = '{}:{}:{}:sent-quantity'.format('VEIL', 'SMS', sms_provider_id)

    @property
    def sms_provider_id(self):
        return self._sms_provider_id

    def get_receiver_list(self, receivers):
        raise NotImplementedError()

    def send(self, receivers, message, sms_code, transactional):
        raise NotImplementedError()

    def query_balance(self):
        raise NotImplementedError()

    def get_minimal_message_quantity(self, message):
        raise NotImplementedError()

    def get_balance_in_redis(self):
        balance = redis().get(self.balance_key_in_redis)
        if balance is not None:
            balance = int(balance)
        return balance

    def set_balance(self, balance):
        redis().setex(self.balance_key_in_redis, SMS_PROVIDER_BALANCE_ALIVE_IN_SECONDS, balance)

    def get_sent_quantity_in_redis(self):
        sent_quantity = redis().get(self.sent_quantity_key_in_redis)
        if sent_quantity is not None:
            sent_quantity = int(sent_quantity)
        return sent_quantity

    def add_sent_quantity(self, quantity):
        redis().incrby(self.sent_quantity_key_in_redis, quantity)
        redis().expire(self.sent_quantity_key_in_redis, SMS_PROVIDER_SENT_QUANTITY_ALIVE_IN_SECONDS)

    def reset_balance_and_sent_quantity(self, balance):
        with redis().pipeline() as pipe:
            pipe.setex(self.balance_key_in_redis, SMS_PROVIDER_BALANCE_ALIVE_IN_SECONDS, balance)
            pipe.setex(self.sent_quantity_key_in_redis, SMS_PROVIDER_SENT_QUANTITY_ALIVE_IN_SECONDS, 0)
            pipe.execute()

    def check_balance_and_reconciliation(self):
        messages = []
        balance = self.query_balance()
        if balance <= SMS_PROVIDER_BALANCE_THRESHOLD:
            messages.append('sms provider-{} balance is less than threshold: {}/{}'.format(self._sms_provider_id, balance, SMS_PROVIDER_BALANCE_THRESHOLD))

        sent_quantity = self.get_sent_quantity_in_redis()
        if sent_quantity is None:
            self.add_sent_quantity(0)
            sent_quantity = 0
        last_balance = self.get_balance_in_redis()
        if last_balance is None:
            self.set_balance(balance)
            last_balance = balance
        provider_sent_quantity = last_balance - balance
        if provider_sent_quantity != sent_quantity:
            LOGGER.info('VEIL SMS RECONCILIATION: %(provider_sent_quantity)s, %(sent_quantity)s, %(diff)s', {
                'provider_sent_quantity': provider_sent_quantity,
                'sent_quantity': sent_quantity,
                'diff': provider_sent_quantity - sent_quantity
            })
            messages.append('sms provider-{} reconciliation failed: {}/{}'.format(self._sms_provider_id, provider_sent_quantity, sent_quantity))

        self.reset_balance_and_sent_quantity(balance)

        return messages


class SendError(Exception):
    pass
