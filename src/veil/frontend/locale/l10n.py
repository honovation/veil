# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import datetime
import pytz
import babel.dates
from veil.utility.clock import DEFAULT_CLIENT_TIMEZONE
from veil.frontend.template import template_filter
from veil.utility.clock import get_current_time
from .i18n import get_current_locale, _

@template_filter('timedelta')
def timedelta_filter(delta, granularity='second', with_direction=False):
    if with_direction:
        if delta >= datetime.timedelta(seconds=0):
            direction = _('后')
        else:
            direction = _('前')
    else:
        direction = ''
    delta_str = format_timedelta(delta, granularity=granularity, locale=get_current_locale())
    return '{}{}'.format(delta_str, direction)


@template_filter('timedelta_by_now')
def timedelta_by_now_filter(value, granularity='second'):
    current_time = get_current_time()
    return timedelta_filter(value - current_time, granularity, with_direction=True)


@template_filter('time')
def time_filter(value, format='medium'):
    return babel.dates.format_time(time=value, format=format, tzinfo=DEFAULT_CLIENT_TIMEZONE,
        locale=get_current_locale())


@template_filter('date')
def date_filter(value, format='medium'):
    return babel.dates.format_date(date=value, format=format, locale=get_current_locale())


@template_filter('datetime')
def datetime_filter(value, format='yyyy-MM-dd HH:mm:ss'):
    if 'epoch' == format:
        epoch = datetime.datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
        delta = value - epoch
        return delta.total_seconds()
    else:
        return babel.dates.format_datetime(datetime=value, format=format, tzinfo=DEFAULT_CLIENT_TIMEZONE,
            locale=get_current_locale())


def parse_epoch_datetime(text):
    if text:
        return datetime.datetime.utcfromtimestamp(float(text)).replace(tzinfo=pytz.utc)
    return None

TIMEDELTA_UNITS = (
    ('year', '年', 3600 * 24 * 365),
    ('month', '月', 3600 * 24 * 30),
    ('week', '周', 3600 * 24 * 7),
    ('day', '天', 3600 * 24),
    ('hour', '小时', 3600),
    ('minute', '分钟', 60),
    ('second', '秒', 1)
    )

def format_timedelta(delta, granularity='second', threshold=.85, locale='zh_CN'):
    """Return a time delta according to the rules of the given locale.
    >>> format_timedelta(timedelta(weeks=12), locale='en_US')
    '3 mths'
    >>> format_timedelta(timedelta(seconds=1), locale='es')
    '1 s'
    The granularity parameter can be provided to alter the lowest unit
    presented, which defaults to a second.

    >>> format_timedelta(timedelta(hours=3), granularity='day',
    ...                  locale='en_US')
    '1 day'
    The threshold parameter can be used to determine at which value the
    presentation switches to the next higher unit. A higher threshold factor
    means the presentation will switch later. For example:
    >>> format_timedelta(timedelta(hours=23), threshold=0.9, locale='en_US')
    '1 day'
    >>> format_timedelta(timedelta(hours=23), threshold=1.1, locale='en_US')
    '23 hrs'
    :param delta: a ``timedelta`` object representing the time difference to
                  format, or the delta in seconds as an `int` value
    :param granularity: determines the smallest unit that should be displayed,
                        the value can be one of "year", "month", "week", "day",
                        "hour", "minute" or "second"
    :param threshold: factor that determines at which point the presentation
                      switches to the next higher unit
    :param locale: a `Locale` object or a locale identifier
    :rtype: `unicode`
    """
    if isinstance(delta, datetime.timedelta):
        seconds = int((delta.days * 86400) + delta.seconds)
    else:
        seconds = int(delta)
    for unit, plural_form, secs_per_unit in TIMEDELTA_UNITS:
        value = abs(seconds) / secs_per_unit
        if value >= threshold or unit == granularity:
            if unit == granularity and value > 0:
                value = max(1, value)
            value = int(round(value))
            return '{}{}'.format(value, plural_form)
    return ''