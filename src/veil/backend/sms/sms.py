# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import random
import logging
from veil.backend.queue import *
from veil.backend.redis import *
from veil.environment import get_application_sms_whitelist
from veil.utility.misc import *
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


def get_current_sms_provider():
    global current_sms_provider
    if not current_sms_provider:
        raise Exception('no current sms provider')
    return current_sms_provider


def register_sms_provider(sms_provider_module):
    sms_provider = sms_provider_module.register()
    if sms_provider.sms_provider_id not in _sms_providers:
        _sms_providers[sms_provider.sms_provider_id] = sms_provider
        global current_sms_provider
        if not current_sms_provider:
            current_sms_provider = sms_provider


def shuffle_current_sms_provider(excluded_provider_ids):
    sms_provider_candidates = [sp for sp in _sms_providers.values() if sp.sms_provider_id not in excluded_provider_ids]
    if not sms_provider_candidates:
        return
    global current_sms_provider
    current_sms_provider = random.choice(sms_provider_candidates)
    return current_sms_provider


@periodic_job('31 6 * * *')
def check_sms_provider_balance_and_reconciliation_job():
    error_messages = []
    for instance in _sms_providers.values():
        error_messages.extend(instance.check_balance_and_reconciliation())
    if error_messages:
        raise Exception(', '.join(error_messages))


@job('send_transactional_sms', retry_every=10, retry_timeout=90)
def send_transactional_sms_job(receivers, message, sms_code, last_sms_code=None, promotional=False):
    sms_provider = get_current_sms_provider()
    receiver_list = get_receiver_list(receivers, sms_provider.max_receiver_count)
    if len(receiver_list) == 1:
        receivers = receiver_list[0]
        send_sms(receivers, message, sms_code, last_sms_code=last_sms_code, promotional=promotional)
        with redis().pipeline() as pipe:
            for receiver in receivers:
                pipe.setex(sent_sms_redis_key(receiver, sms_code), SENT_SMS_RECORD_ALIVE_IN_SECONDS, sms_provider.sms_provider_id)
            pipe.execute()
    else:
        for receivers_ in receiver_list:
            queue().enqueue(send_transactional_sms_job, receivers=receivers_, message=message, sms_code=sms_code, last_sms_code=last_sms_code,
                            promotional=promotional)


@job('send_slow_transactional_sms', retry_every=10 * 60, retry_timeout=3 * 60 * 60)
def send_slow_transactional_sms_job(receivers, message, sms_code, promotional=False):
    sms_provider = get_current_sms_provider()
    receiver_list = get_receiver_list(receivers, sms_provider.max_receiver_count)
    if len(receiver_list) == 1:
        receivers = receiver_list[0]
        send_sms(receivers, message, sms_code, promotional=promotional)
    else:
        for receivers_ in receiver_list:
            queue().enqueue(send_slow_transactional_sms_job, receivers=receivers_, message=message, sms_code=sms_code, promotional=promotional)


@job('send_marketing_sms', retry_every=10 * 60, retry_timeout=3 * 60 * 60)
def send_marketing_sms_job(receivers, message, sms_code, promotional=False):
    sms_provider = get_current_sms_provider()
    receiver_list = get_receiver_list(receivers, sms_provider.max_receiver_count)
    if len(receiver_list) == 1:
        receivers = receiver_list[0]
        send_sms(receivers, message, sms_code, transactional=False, promotional=promotional)
    else:
        for receivers_ in receiver_list:
            queue().enqueue(send_marketing_sms_job, receivers=receivers_, message=message, sms_code=sms_code, promotional=promotional)


@job('send_transactional_sms', retry_every=10, retry_timeout=90)
def send_voice_validation_code_job(receiver, code, sms_code, last_sms_code=None):
    used_sms_provider_ids = set()
    if last_sms_code:
        last_sms_provider_id = redis().get(sent_sms_redis_key(receiver, last_sms_code))
        if last_sms_provider_id:
            used_sms_provider_ids.add(int(last_sms_provider_id))
            shuffle_current_sms_provider(used_sms_provider_ids)
    sms_provider = get_current_sms_provider()
    while True:
        if not sms_provider.support_voice:
            used_sms_provider_ids.add(sms_provider.sms_provider_id)
            sms_provider = shuffle_current_sms_provider(used_sms_provider_ids)
            if not sms_provider:
                raise Exception('not enough reliable sms voice providers')
            continue
        try:
            sms_provider.send_voice(receiver, code, sms_code)
        except SendError as e:
            retry_receivers = e.get_send_failed_mobiles()
            if not retry_receivers:
                return
            receiver = retry_receivers
            used_sms_provider_ids.add(current_sms_provider.sms_provider_id)
            sms_provider = shuffle_current_sms_provider(used_sms_provider_ids)
            if not sms_provider:
                raise Exception('not enough reliable sms providers')
        else:
            current_sms_provider.add_sent_quantity(1)
            break


def send_sms(receivers, message, sms_code, last_sms_code=None, transactional=True, promotional=False):
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
            receivers = set(receivers)
            receivers -= receivers_not_in_whitelist
            if not receivers:
                return
    sms_provider = get_current_sms_provider()
    while True:
        sent_receivers, need_retry_receivers = sms_provider.send(receivers, message, sms_code, transactional, promotional=promotional)
        if sent_receivers:
            sms_provider.add_sent_quantity(sms_provider.get_minimal_message_quantity(message) * len(sent_receivers))

        if not need_retry_receivers:
            break
        elif transactional:
            raise Exception('sms send transactional failed: {}'.format(need_retry_receivers))
        else:
            receivers = need_retry_receivers
            used_sms_provider_ids.add(sms_provider.sms_provider_id)
            sms_provider = shuffle_current_sms_provider(used_sms_provider_ids)
            if not sms_provider:
                raise Exception('not enough reliable sms providers')


def get_receiver_list(receivers, max_receiver_count):
    if isinstance(receivers, basestring):
        receivers = [receivers]
    receivers = list(set(receivers))
    return [r for r in chunks(receivers, max_receiver_count)]


class SMService(object):
    def __init__(self, sms_provider_id, max_receiver_count, support_voice=False):
        self._sms_provider_id = sms_provider_id
        self._max_receiver_count = max_receiver_count
        self.support_voice = support_voice
        self.balance_key_in_redis = 'VEIL:SMS:{}:balance'.format(sms_provider_id)
        self.sent_quantity_key_in_redis = 'VEIL:SMS:{}:sent-quantity'.format(sms_provider_id)

    @property
    def sms_provider_id(self):
        return self._sms_provider_id

    @property
    def max_receiver_count(self):
        return self._max_receiver_count

    def send(self, receivers, message, sms_code, transactional, promotional=False):
        raise NotImplementedError()

    def send_voice(self, receiver, code, sms_code):
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
    def __init__(self, message, mobiles):
        super(SendError, self).__init__(message, mobiles)
        self.mobiles = mobiles

    def get_send_failed_mobiles(self):
        return self.mobiles
