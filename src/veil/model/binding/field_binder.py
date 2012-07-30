# -*- coding: utf-8 -*-
"""
field binder takes single value and returns transformed single value in expected case
otherwise throw Invalid exception
"""
from __future__ import unicode_literals, print_function, division
import re
from datetime import datetime, time
import pytz
from pytz import timezone, UnknownTimeZoneError
from dateutil.parser import parse
from veil.model.binding.invalid import Invalid


_EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9_=%.+-]+@([a-zA-Z0-9_=%+-]+\.)+[a-zA-Z]{2,6}$')

# reference to http://www.cnfgg.com/article/Asp/Asp_phoneCheck.htm
_MOBILE_PATTERN = re.compile(r'^0?1[3458]\d{9}$')
_LANDLIINE_PATTERN = re.compile(r'^(\d{2,4}[-.\s_－—]?)?\d{3,8}([-.\s_－—]?\d{3,8})?([-.\s_－—]?\d{1,7})?$')


def anything(value):
    return value


def is_not(v):
    def bind(value):
        if value == bind.v:
            raise Invalid('{}{}'.format(_('must not be: '), bind.v))
        return value
    bind.v = v
    return bind


def not_empty(value):
    if value is not None and value != '':
        return value
    raise Invalid(_('must not be empty'))


def is_list(value):
    if isinstance(value, (list, tuple)):
        return value
    raise Invalid(_('not list'))


def one_of(seq):
    assert seq is not None
    def bind(value):
        if value not in bind.seq:
            raise Invalid(_('must be one of valid values'))
        return value
    bind.seq = seq
    return bind


def is_email(value):
    if _EMAIL_PATTERN.match(value) is None:
        raise Invalid(_('not a well-formed email'))
    return value


def is_mobile(value):
    if _MOBILE_PATTERN.match(value) is None:
        raise Invalid(_('not a well-formed mobile'))
    return value


def is_landline(value):
    if _LANDLIINE_PATTERN.match(value) is None:
        raise Invalid(_('not a well-formed mobile'))
    return value


def to_integer(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise Invalid(_('not an integer'))


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise Invalid(_('not a float'))


def to_bool(value):
    if value in ['0', 'false', 'False']:
        return False
    return bool(value)


def to_time(value):
    try:
        dt = datetime.strptime(value, '%I:%M %p')
    except ValueError:
        raise Invalid(_('Invalid time format'))
    else:
        return time(dt.hour, dt.minute)


def to_date(format='%Y-%m-%d'):
    def bind(value):
        if isinstance(value, datetime):
            return value.date()
        try:
            dt = datetime.strptime(value, bind.format)
        except ValueError:
            raise Invalid(_('Invalid date format'))
        else:
            return dt.date()
    bind.format = format
    return bind


def to_datetime_via_parse(value):
    try:
        return parse(value, yearfirst=True)
    except ValueError:
        raise Invalid(_('Invalid datetime format'))


def to_datetime(format='%Y-%m-%d %H:%M:%S'):
    def bind(value):
        if isinstance(value, datetime):
            return value
        else:
            try:
                return datetime.strptime(value, bind.format)
            except ValueError:
                raise Invalid(_('Invalid datetime format'))
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
            raise Exception('Unable to parse date string %r' % value)
        groups = m.groupdict()
        hours, minutes = int(groups['hours']), int(groups['minutes'])
        if groups['prefix'] == '-':
            hours = -hours
            minutes = -minutes
        tz = pytz.FixedOffset(hours * 60 + minutes)
        return datetime(int(groups['year']), int(groups['month']), int(groups['day']), int(groups['hour']),
            int(groups['minute']), tzinfo=tz)
    except:
        raise Invalid(_('Invalid ISO8601 datetime format'))


def to_timezone(value):
    try:
        return timezone(value)
    except UnknownTimeZoneError:
        raise Invalid(_('Invalid timezone'))


def clamp_length(min=None, max=None):
    """
    clamp a value between minimum and maximum lengths (either
    of which are optional).
    """
    def bind(value):
        value_length = len(value)
        if bind.min is not None and value_length < bind.min:
            raise Invalid(_('too short'))
        if bind.max is not None and value_length > bind.max:
            raise Invalid(_('too long'))
        return value
    bind.min = min
    bind.max = max
    return bind


def not_duplicate(value):
    if len(set(value)) != len(value):
        raise Invalid(_('Duplicate item not allowed'))
    return value