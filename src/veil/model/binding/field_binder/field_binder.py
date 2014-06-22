# -*- coding: UTF-8 -*-
"""
field binder takes single value and returns transformed single value in expected case
otherwise throw Invalid exception
"""
from __future__ import unicode_literals, print_function, division
import re
from datetime import datetime, date, time
import pytz
from dateutil.parser import parse
from decimal import Decimal, InvalidOperation
import sys
from veil.utility.clock import *
from ..invalid import Invalid

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9_=%.+-]+@([a-zA-Z0-9_=%+-]+\.)+[a-zA-Z]{2,6}$')
PASSWORD_PATTERN = re.compile(r'[A-Za-z0-9`~!@#$%^&*()=+\-\[\]\{\};:,\/?.]{8,16}')
# reference to http://www.cnfgg.com/article/Asp/Asp_phoneCheck.htm
MOBILE_PATTERN = re.compile(r'^1[34578]\d{9}$') # can reference to 支付宝账户支持绑定的手机号段有哪些？(http://help.alipay.com/lab/help_detail.htm?help_id=255119)
LANDLIINE_PATTERN = re.compile(r'^(\d{2,4}[-.\s_－—]?)?\d{3,8}([-.\s_－—]?\d{3,8})?([-.\s_－—]?\d{1,7})?$')


def anything(value):
    return value

def remove_chars(chars='-'):
    def bind(value):
        if value:
            value = value.translate({ord(c): None for c in bind.chars})
        return value
    bind.chars = chars
    return bind

def is_not(v):
    def bind(value):
        if value == bind.v:
            raise Invalid('{}{}'.format(_('不能是：'), bind.v))
        return value
    bind.v = v
    return bind


def not_empty(value):
    if value not in (None, '', [], (), {}, set()):
        return value
    raise Invalid(_('不能为空'))


def match(pattern):
    def bind(value):
        r = re.compile(pattern)
        if r.match(value) is None:
            raise Invalid(_('格式不正确'))
        return value
    return bind

def is_list(value):
    if isinstance(value, (list, tuple)):
        return value
    raise Invalid(_('值不为列表'))


def one_of(seq):
    assert seq is not None
    def bind(value):
        if value not in bind.seq:
            raise Invalid(_('值不在范围之内'))
        return value
    bind.seq = seq
    return bind


def is_email(value, return_none_when_invalid=False):
    if EMAIL_PATTERN.match(value) is None:
        if return_none_when_invalid:
            return None
        else:
            raise Invalid(_('不是有效的电子邮件地址'))
    return value


def is_mobile(value, return_none_when_invalid=False):
    if MOBILE_PATTERN.match(value) is None:
        if return_none_when_invalid:
            return None
        else:
            raise Invalid(_('不是有效的移动电话号码'))
    return value

def valid_password(value):
    if PASSWORD_PATTERN.match(value) is None:
        raise Invalid(_('密码不符合规范'))
    return value

def is_landline(value, return_none_when_invalid=False):
    if LANDLIINE_PATTERN.match(value) is None:
        if return_none_when_invalid:
            return None
        else:
            raise Invalid(_('不是有效的座机号码'))
    return value


def to_integer(value, return_none_when_invalid=False):
    try:
        return int(value)
    except (TypeError, ValueError):
        if return_none_when_invalid:
            return None
        else:
            raise Invalid(_('不是整数'))


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise Invalid(_('数据不合法'))


def to_decimal(value):
    try:
        return Decimal(value)
    except (TypeError, ValueError, InvalidOperation):
        raise Invalid(_('数据不合法'))


def to_bool(value):
    if isinstance(value, basestring) and value.lower() in ['0', 'f', 'false']:
        return False
    return bool(value)


def to_time(format='%H:%M:%S', naive=True):
    def bind(value, return_none_when_invalid=False):
        if isinstance(value, datetime):
            return (convert_datetime_to_naive_local(value) if naive else convert_datetime_to_utc_timezone(value)).time()
        elif isinstance(value, time):
            return convert_datetime_to_naive_local(value) if naive else convert_datetime_to_utc_timezone(value)
        try:
            dt = datetime.strptime(value, bind.format)
        except (TypeError, ValueError):
            if return_none_when_invalid:
                return None
            else:
                raise Invalid(_('不是有效的时间'))
        else:
            if not naive:
                dt = convert_datetime_to_utc_timezone(dt)
            return dt.time()
    bind.format = format
    return bind


def to_date(format='%Y-%m-%d', naive=True, return_none_when_invalid=False):
    def bind(value):
        if isinstance(value, datetime):
            return (convert_datetime_to_naive_local(value) if naive else convert_datetime_to_utc_timezone(value)).date()
        elif isinstance(value, date):
            return value
        try:
            dt = datetime.strptime(value, bind.format)
        except (TypeError, ValueError):
            if return_none_when_invalid:
                return None
            else:
                raise Invalid(_('不是有效的日期'))
        else:
            return dt.date()
    bind.format = format
    return bind


def to_datetime_via_parse(value):
    try:
        return parse(value, yearfirst=True)
    except (TypeError, ValueError):
        raise Invalid(_('不是有效的日期时间'))


def to_datetime(format='%Y-%m-%d %H:%M:%S', naive=False):
    def bind(value):
        if isinstance(value, datetime):
            return convert_datetime_to_naive_local(value) if naive else convert_datetime_to_utc_timezone(value)
        else:
            if not value:
                raise Invalid(_('不是有效的日期时间'))
            try:
                dt = datetime.strptime(value, bind.format)
            except (TypeError, ValueError):
                raise Invalid(_('不是有效的日期时间'))
            else:
                if not naive:
                    dt = convert_datetime_to_utc_timezone(dt)
                return dt
    bind.format = format
    return bind


ISO8601_REGEX = re.compile(r'(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2}) (?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}) ?(?P<prefix>[+-])(?P<hours>[0-9]{2}):?(?P<minutes>[0-9]{2})')

def to_datetime_with_minute_precision_from_iso8601(value):
    """
    Valid formats:
        YYYY-MM-DD hh:mm ±hh:mm
        YYYY-MM-DD hh:mm ±hhmm
        YYYY-MM-DD hh:mm±hhmm
    """
    try:
        m = ISO8601_REGEX.match(value)
        if not m:
            raise Exception('Unable to parse date string {!r}'.format(value))
        groups = m.groupdict()
        hours, minutes = int(groups['hours']), int(groups['minutes'])
        if groups['prefix'] == '-':
            hours = -hours
            minutes = -minutes
        tz = pytz.FixedOffset(hours * 60 + minutes)
        return datetime(int(groups['year']), int(groups['month']), int(groups['day']), int(groups['hour']),
            int(groups['minute']), tzinfo=tz)
    except:
        raise Invalid(_('不是有效的日期时间'))


def to_timezone(value):
    try:
        return pytz.timezone(value)
    except pytz.UnknownTimeZoneError:
        raise Invalid(_('不是有效的时区'))


def clamp_length(min=None, max=None):
    """
    clamp a value between minimum and maximum lengths (either
    of which are optional).
    """
    def bind(value):
        value_length = len(value)
        if bind.min is not None and value_length < bind.min:
            raise Invalid(_('长度不小于') + str(bind.min) + _('，现在长度为：') + str(value_length))
        if bind.max is not None and value_length > bind.max:
            raise Invalid(_('长度不大于') + str(bind.max) + _('，现在长度为：') + str(value_length))
        return value
    bind.min = min
    bind.max = max
    return bind

def clamp(min=None, max=None, include_min=True, include_max=True):
    """
    clamp a value between minimum and maximum (either
    of which are optional).
    """
    def bind(value):
        if bind.min is not None and (value < bind.min or not include_min and value == bind.min):
            raise Invalid(_('值超出范围'))
        if bind.max is not None and (value > bind.max or not include_max and value == bind.max):
            raise Invalid(_('值超出范围'))
        return value
    bind.min = min
    bind.max = max
    return bind


def not_duplicate(value):
    if len(set(value)) != len(value):
        raise Invalid(_('有重复值'))
    return value


def _(*args, **kwargs):
# to supress the warning of pycharm
    return sys.modules['__builtin__']._(*args, **kwargs)
