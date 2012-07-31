from __future__ import unicode_literals, print_function, division
import babel.dates
import pytz
from veil.frontend.template import template_filter
from sandal.clock import get_current_time
from .i18n import get_current_locale, _

DEFAULT_CLIENT_TIMEZONE = pytz.timezone('Asia/Shanghai')

@template_filter
def timedelta(value):
    current_time = get_current_time()
    if current_time > value:
        delta = current_time - value
        direction = _(' ago')
    else:
        delta = value - current_time
        direction = _(' later')
    delta_str = babel.dates.format_timedelta(delta, locale=get_current_locale())
    return '{}{}'.format(delta_str, direction)


@template_filter
def time(value, format='medium'):
    return babel.dates.format_time(time=value, format=format, tzinfo=DEFAULT_CLIENT_TIMEZONE,
                                   locale=get_current_locale())


@template_filter
def date(value, format='medium'):
    return babel.dates.format_date(date=value, format=format, locale=get_current_locale())


@template_filter
def datetime(value, format='medium'):
    return babel.dates.format_datetime(datetime=value, format=format, tzinfo=DEFAULT_CLIENT_TIMEZONE,
                                       locale=get_current_locale())
