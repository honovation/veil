# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import random
import logging
from collections import OrderedDict
from veil_component import VEIL_ENV
from veil.environment import get_application_sms_whitelist
from veil.backend.job_queue import *
from veil.backend.redis import *
from veil.model.collection import *
from veil.utility.json import *
from veil.utility.misc import *

LOGGER = logging.getLogger(__name__)

redis = register_redis('persist_store')

_sms_providers = OrderedDict()
CURRENT_SMS_PROVIDER_ID_KEY = 'VEIL:SMS:CURRENT-SMS-PROVIDER-ID'
CURRENT_SMS_PROVIDER_ALIVE_TIME_IN_SECONDS = 10 * 60
SENT_SMS_RECORD_ALIVE_IN_SECONDS = 60 * 60
SMS_PROVIDER_BALANCE_THRESHOLD = 2000
SMS_PROVIDER_BALANCE_ALIVE_IN_SECONDS = 60 * 60 * 36
SMS_PROVIDER_SENT_QUANTITY_ALIVE_IN_SECONDS = 60 * 60 * 36


def sent_sms_redis_key(mobile, sms_code):
    return '{}:{}'.format(mobile, sms_code)


def get_current_sms_provider():
    if not _sms_providers:
        raise Exception('no sms provider')
    current_sms_provider_id = redis().get(CURRENT_SMS_PROVIDER_ID_KEY)
    if not current_sms_provider_id:
        current_sms_provider_id = _sms_providers.keys()[0]
        redis().setex(CURRENT_SMS_PROVIDER_ID_KEY, CURRENT_SMS_PROVIDER_ALIVE_TIME_IN_SECONDS, current_sms_provider_id)
    sms_provider = _sms_providers[int(current_sms_provider_id)]
    return sms_provider


def register_sms_provider(sms_provider_module):
    sms_provider = sms_provider_module.register()
    if sms_provider.sms_provider_id not in _sms_providers:
        _sms_providers[sms_provider.sms_provider_id] = sms_provider


def shuffle_current_sms_provider(excluded_provider_ids):
    sms_provider_candidates = [sp for sp in _sms_providers.values() if sp.sms_provider_id not in excluded_provider_ids]
    if not sms_provider_candidates:
        raise Exception('not enough sms/voice provider to switch')
    sms_provider = random.choice(sms_provider_candidates)
    redis().setex(CURRENT_SMS_PROVIDER_ID_KEY, CURRENT_SMS_PROVIDER_ALIVE_TIME_IN_SECONDS, sms_provider.sms_provider_id)
    return sms_provider


@task(queue='check_sms_provider_balance_and_reconciliation', schedule=cron_expr('31 6 * * *'))
def check_sms_provider_balance_and_reconciliation():
    error_messages = []
    for instance in _sms_providers.values():
        error_messages.extend(instance.check_balance_and_reconciliation())
    if error_messages:
        raise Exception(', '.join(error_messages))


def send_validation_code_via_sms(receivers, sms_code, last_sms_code=None, message=None, template=None, expired_at=None):
    send_sms(receivers, sms_code, transactional=True, promotional=False, last_sms_code=last_sms_code, message=message, template=template, expired_at=expired_at)


def send_validation_code_via_voice(receiver, code, sms_code, last_sms_code=None, expired_at=None):
    send_voice_validation_code.delay(receiver, code, sms_code, last_sms_code=last_sms_code, expired_at=expired_at)


def send_sms(receivers, sms_code, transactional=False, promotional=True, last_sms_code=None, message=None, template=None, expired_at=None):
    assert message is not None or template is not None, 'message or template must be provided'
    json_template = to_json(template)
    if transactional:
        if promotional:
            send_slow_transactional_sms.delay(receivers, sms_code, promotional, message=message, template=json_template, expired_at=expired_at)
        else:
            send_transactional_sms.delay(receivers, sms_code, promotional, last_sms_code=last_sms_code, message=message, template=json_template,
                                         expired_at=expired_at)
    else:
        send_marketing_sms.delay(receivers, sms_code, promotional, message=message, template=json_template, expired_at=expired_at)


@task(queue='send_transactional_sms', retry_method=fixed(10, 10))
def send_transactional_sms(receivers, sms_code, promotional, last_sms_code=None, message=None, template=None):
    sms_provider = get_current_sms_provider()
    receiver_list = get_receiver_list(receivers, sms_provider.max_receiver_count)
    if len(receiver_list) == 1:
        receivers = receiver_list[0]
        send(receivers, sms_code, last_sms_code=last_sms_code, promotional=promotional, message=message, template=template)
        with redis().pipeline() as pipe:
            for receiver in receivers:
                pipe.setex(sent_sms_redis_key(receiver, sms_code), SENT_SMS_RECORD_ALIVE_IN_SECONDS, sms_provider.sms_provider_id)
            pipe.execute()
    else:
        for receivers_ in receiver_list:
            send_transactional_sms.delay(receivers_, sms_code, promotional, last_sms_code=last_sms_code, message=message, template=template)


@task(queue='send_slow_transactional_sms', retry_method=fixed(60 * 10, 18))
def send_slow_transactional_sms(receivers, sms_code, promotional, message=None, template=None):
    sms_provider = get_current_sms_provider()
    receiver_list = get_receiver_list(receivers, sms_provider.max_receiver_count)
    if len(receiver_list) == 1:
        receivers = receiver_list[0]
        send(receivers, sms_code, promotional=promotional, message=message, template=template)
    else:
        for receivers_ in receiver_list:
            send_slow_transactional_sms.delay(receivers_, sms_code, promotional, message=message, template=template)


@task(queue='send_marketing_sms', retry_method=fixed(60 * 10, 18))
def send_marketing_sms(receivers, sms_code, promotional, message=None, template=None):
    sms_provider = get_current_sms_provider()
    receiver_list = get_receiver_list(receivers, sms_provider.max_receiver_count)
    if len(receiver_list) == 1:
        receivers = receiver_list[0]
        send(receivers, sms_code, transactional=False, promotional=promotional, message=message, template=template)
    else:
        for receivers_ in receiver_list:
            send_marketing_sms.delay(receivers_, sms_code, promotional, message=message, template=template)


@task(queue='send_voice_validation_code', retry_method=fixed(10, 10))
def send_voice_validation_code(receiver, code, sms_code, last_sms_code=None):
    used_sms_provider_ids = set()
    sms_provider = None
    if last_sms_code:
        last_sms_provider_id = redis().get(sent_sms_redis_key(receiver, last_sms_code))
        if last_sms_provider_id:
            used_sms_provider_ids.add(int(last_sms_provider_id))
            sms_provider = shuffle_current_sms_provider(used_sms_provider_ids)
    sms_provider = sms_provider or get_current_sms_provider()
    while True:
        if not sms_provider.support_voice:
            used_sms_provider_ids.add(sms_provider.sms_provider_id)
            sms_provider = shuffle_current_sms_provider(used_sms_provider_ids)
            continue
        try:
            sms_provider.send_voice(receiver, code, sms_code)
        except SendError as e:
            retry_receivers = e.get_send_failed_mobiles()
            if not retry_receivers:
                return
            receiver = retry_receivers
            used_sms_provider_ids.add(sms_provider.sms_provider_id)
            sms_provider = shuffle_current_sms_provider(used_sms_provider_ids)
        else:
            sms_provider.add_sent_quantity(1)
            break


def send(receivers, sms_code, last_sms_code=None, transactional=True, promotional=True, message=None, template=None):
    used_sms_provider_ids = set()
    sms_provider = None
    if last_sms_code:
        last_sms_provider_id = redis().get(sent_sms_redis_key(receivers[0], last_sms_code))
        if last_sms_provider_id:
            used_sms_provider_ids.add(int(last_sms_provider_id))
            sms_provider = shuffle_current_sms_provider(used_sms_provider_ids)
    if not VEIL_ENV.is_prod:
        receivers_not_in_whitelist = set(r for r in receivers if r not in get_application_sms_whitelist())
        if receivers_not_in_whitelist:
            LOGGER.warn('Ignored sms receivers not in the whitelist under non-public env: %(receivers_not_in_whitelist)s', {
                'receivers_not_in_whitelist': receivers_not_in_whitelist
            })
            receivers = set(receivers)
            receivers -= receivers_not_in_whitelist
            if not receivers:
                return
    sms_provider = sms_provider or get_current_sms_provider()
    while True:
        sent_receivers, need_retry_receivers = sms_provider.send(receivers, sms_code, transactional, promotional, message=message,
                                                                 template=objectify(from_json(template)))
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


def get_receiver_list(receivers, max_receiver_count):
    if isinstance(receivers, basestring):
        receivers = [receivers]
    receivers = list(set(receivers))
    return [r for r in chunks(receivers, max_receiver_count)]


class SMService(object):
    def __init__(self, sms_provider_id, max_receiver_count, support_voice=False, support_query_balance=True):
        self._sms_provider_id = sms_provider_id
        self._max_receiver_count = max_receiver_count
        self.support_voice = support_voice
        self.support_query_balance = support_query_balance
        self.balance_key_in_redis = 'VEIL:SMS:{}:balance'.format(sms_provider_id)
        self.sent_quantity_key_in_redis = 'VEIL:SMS:{}:sent-quantity'.format(sms_provider_id)

    @property
    def sms_provider_id(self):
        return self._sms_provider_id

    @property
    def max_receiver_count(self):
        return self._max_receiver_count

    def send(self, receivers, sms_code, transactional, promotional, message=None, template=None):
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
        if not self.support_query_balance:
            sent_quantity = self.get_sent_quantity_in_redis()
            LOGGER.info('sms provider sent quantity: %(sms_provider_id)s, %(sent_quantity)s', {
                'sms_provider_id': self.sms_provider_id,
                'sent_quantity': sent_quantity
            })
            self.reset_balance_and_sent_quantity(0)
            return messages
        balance = self.query_balance()
        if balance <= SMS_PROVIDER_BALANCE_THRESHOLD:
            messages.append('sms provider-{} balance is less than threshold: {}/{}'.format(self.sms_provider_id, balance, SMS_PROVIDER_BALANCE_THRESHOLD))

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
            messages.append('sms provider-{} reconciliation failed: {}/{}'.format(self.sms_provider_id, provider_sent_quantity, sent_quantity))

        self.reset_balance_and_sent_quantity(balance)

        return messages


class SendError(Exception):
    def __init__(self, message, mobiles):
        super(SendError, self).__init__(message, mobiles)
        self.mobiles = mobiles

    def get_send_failed_mobiles(self):
        return self.mobiles
