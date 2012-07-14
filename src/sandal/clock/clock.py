from __future__ import unicode_literals, print_function, division
import contextlib
from datetime import datetime
import calendar
import pytz

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