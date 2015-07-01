# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from datetime import datetime, timedelta
import pytz
import babel.dates
from veil.frontend.template import *
from veil.utility.clock import *
from .i18n import get_current_locale, _


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


def parse_epoch_datetime(text):
    if text:
        return datetime.utcfromtimestamp(float(text)).replace(tzinfo=pytz.utc)
    return None
