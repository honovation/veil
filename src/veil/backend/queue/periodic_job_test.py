from __future__ import unicode_literals, print_function, division
import calendar
from datetime import timedelta, datetime
import pytz
from unittest.case import TestCase
from veil.utility.clock import require_current_time_being
from .periodic_job import TimedeltaSchedule
from .periodic_job import CroniterSchedule

class TimedeltaScheduleTest(TestCase):
    def test_zero_timedelta(self):
        with self.assertRaises(Exception):
            TimedeltaSchedule(timedelta(0))

    def test_get_next_timestamp(self):
        dt = datetime(2008, 8, 8, 8, 5, 0, tzinfo=pytz.utc)
        dt_timestamp = calendar.timegm(dt.utctimetuple())

        next_timestamp = TimedeltaSchedule(timedelta(minutes=1)).get_next_timestamp(dt_timestamp)
        self.assertEqual(dt_timestamp + 60, next_timestamp)

        with require_current_time_being(dt):
            next_timestamp = TimedeltaSchedule(timedelta(minutes=1)).get_next_timestamp()
            self.assertEqual(dt_timestamp + 60, next_timestamp)

class CroniterScheduleTest(TestCase):
    def test_invalid_expression(self):
        with self.assertRaises(Exception):
            CroniterSchedule('abc')

    def test_get_next_timestamp(self):
        dt = datetime(2008, 8, 8, 8, 5, 0, tzinfo=pytz.utc)
        dt_timestamp = calendar.timegm(dt.utctimetuple())
        expected_next_timestamp = calendar.timegm(datetime(2008, 8, 8, 8, 10, 0, tzinfo=pytz.utc).utctimetuple())

        next_timestamp = CroniterSchedule('*/5 * * * *').get_next_timestamp(dt_timestamp)
        self.assertEqual(expected_next_timestamp, next_timestamp)

        with require_current_time_being(dt):
            next_timestamp = CroniterSchedule('*/5 * * * *').get_next_timestamp()
            self.assertEqual(expected_next_timestamp, next_timestamp)
