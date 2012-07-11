from __future__ import unicode_literals, print_function, division
import contextlib
from datetime import datetime
import calendar
from dateutil.parser import parse
import pytz

__all__ = [
    'require_current_time_being',
    'get_current_time',
    'parse_datetime',
    'convert_datetime_to_default_client_timezone',
    'convert_naive_datetime_to_default_client_timezone',
    ]

DEFAULT_CLIENT_TIMEZONE = pytz.timezone('Asia/Shanghai')

current_time = None

@contextlib.contextmanager
def require_current_time_being(time):
    assert time.tzinfo, 'must be explicit with time zone'
    global current_time
    current_time = time
    try:
        yield
    finally:
        current_time = None


def get_current_time():
    return current_time or datetime.now(pytz.utc)


def get_current_timestamp():
    """
    Caveat: the guaranteed precision of timestamp is 1 second
    """
    return calendar.timegm(get_current_time().utctimetuple())


def convert_datetime_to_timestamp(dt):
    return calendar.timegm(dt.utctimetuple())


def convert_timestamp_to_utc_datetime(timestamp):
    return datetime.fromtimestamp(timestamp, pytz.utc)


def convert_datetime_to_naive_local(dt):
    return datetime.fromtimestamp(convert_datetime_to_timestamp(dt))


def parse_datetime(dtstr):
    return parse(dtstr, yearfirst=True)


def convert_datetime_to_default_client_timezone(dt):
    return convert_datetime_to_timezone(dt, DEFAULT_CLIENT_TIMEZONE)


def convert_datetime_to_timezone(dt, tzinfo):
    assert dt.tzinfo is not None
    converted = dt.astimezone(tzinfo)
    if hasattr(tzinfo, 'normalize'): # pytz
        converted = tzinfo.normalize(converted)
    return converted


def convert_naive_datetime_to_default_client_timezone(dt):
    return convert_naive_datetime_to_timezone(dt, DEFAULT_CLIENT_TIMEZONE)


def convert_naive_datetime_to_timezone(dt, tzinfo):
    assert dt.tzinfo is None
    if hasattr(tzinfo, 'localize'): # pytz
        converted = tzinfo.localize(dt)
    else:
        converted = dt.replace(tzinfo=tzinfo)
    return converted