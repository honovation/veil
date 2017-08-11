# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division

from datetime import datetime, timedelta

import babel.dates

from veil.frontend.template import *
from veil.utility.clock import *
from veil.utility.encoding import *
from .i18n import get_current_locale


@template_filter('timedelta')
def timedelta_filter(delta, granularity='second', add_direction=False):
    if isinstance(delta, basestring):
        return delta
    return babel.dates.format_timedelta(delta, granularity=granularity, threshold=.95, add_direction=add_direction, locale=get_current_locale())


@template_filter('timedelta_by_now')
def timedelta_by_now_filter(value, granularity='second'):
    if isinstance(value, basestring):
        return value
    if value and is_naive_datetime(value):
        value = convert_naive_datetime_to_aware(value)
    current_time = get_current_time()
    return timedelta_filter(value - current_time, granularity, add_direction=True)


@template_filter('time')
def time_filter(value, format='HH:mm:ss'):
    if isinstance(value, basestring):
        return value
    if isinstance(value, datetime):
        if is_naive_datetime(value):
            value = convert_naive_datetime_to_aware(value)
    return babel.dates.format_time(time=value, format=format, tzinfo=DEFAULT_CLIENT_TIMEZONE, locale=get_current_locale())


@template_filter('date')
def date_filter(value, format='yyyy-MM-dd', delta=0):
    if isinstance(value, basestring):
        return value
    date_to_show = value + timedelta(days=delta)
    if isinstance(date_to_show, datetime):
        date_to_show = convert_datetime_to_client_timezone(date_to_show)
    return babel.dates.format_date(date=date_to_show, format=format, locale=get_current_locale())


@template_filter('datetime')
def datetime_filter(value, format='yyyy-MM-dd HH:mm:ss'):
    if isinstance(value, basestring):
        return value
    if value and is_naive_datetime(value):
        value = convert_naive_datetime_to_aware(value)
    if 'epoch' == format:
        epoch = datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
        delta = value - epoch
        return delta.total_seconds()
    else:
        return babel.dates.format_datetime(datetime=value, format=format, tzinfo=DEFAULT_CLIENT_TIMEZONE, locale=get_current_locale())


@template_filter('datetime_range')
def render_datetime_range(datetime_range, include_start=True, include_end=False):
    start_time, end_time = datetime_range
    start_time = convert_datetime_to_client_timezone(start_time)
    end_time = convert_datetime_to_client_timezone(end_time)
    start_time_precision = get_time_precision(start_time)
    end_time_precision = get_time_precision(end_time)
    time_precision = min(start_time_precision, end_time_precision)
    if not include_start and start_time_precision == time_precision:
        start_time = adjust_datetime(start_time, start_time_precision, 1)
    if not include_end and end_time_precision == time_precision:
        end_time = adjust_datetime(end_time, end_time_precision, -1)
    if time_precision == 0:
        time_format = ' %H:%M:%S'
    elif time_precision == 1:
        time_format = ' %H:%M'
    elif time_precision == 2:
        time_format = ' %H点'
    else:
        time_format = ''
    current_time = get_current_time_in_client_timezone()
    if start_time == end_time:
        if time_precision == 3:
            if start_time.year == current_time.year:
                time_format = '%m-%d'
            else:
                time_format = '%Y-%m-%d'
        else:
            if start_time.date() == current_time.date():
                time_format = time_format
            if start_time.year != current_time.year:
                time_format = '%Y-%m-%d{}'.format(time_format)
            else:
                time_format = '%m-%d{}'.format(time_format)
        time_format = to_str(time_format)
        return to_unicode(start_time.strftime(time_format))
    if start_time.year == current_time.year and start_time.year == end_time.year:
        time_format = '%m-%d{}'.format(time_format)
    else:
        time_format = '%Y-%m-%d{}'.format(time_format)
    time_format = to_str(time_format)
    return to_unicode(to_str('{}～{}').format(start_time.strftime(time_format), end_time.strftime(time_format)))


def adjust_datetime(dt, time_precision, delta):
    if time_precision == 0:
        return dt + timedelta(seconds=delta)
    elif time_precision == 1:
        return dt + timedelta(minutes=delta)
    elif time_precision == 2:
        return dt + timedelta(hours=delta)
    elif time_precision == 3:
        return dt + timedelta(days=delta)


def get_time_precision(dt):
    if dt.second != 0:
        return 0
    elif dt.minute != 0:
        return 1
    elif dt.hour != 0:
        return 2
    else:
        return 3


def parse_epoch_datetime(text):
    if text:
        return datetime.utcfromtimestamp(float(text)).replace(tzinfo=pytz.utc)
    return None
