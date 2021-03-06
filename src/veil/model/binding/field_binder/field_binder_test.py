# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import __builtin__
from veil.development.test import TestCase
from .field_binder import *


class FieldBinderTest(TestCase):
    def setUp(self):
        super(FieldBinderTest, self).setUp()
        __builtin__.__dict__['_'] = lambda msg: msg

    def test_duplicate_validator(self):
        with self.assertRaises(Invalid):
            not_duplicate(['USD', 'USD'])

    def test_well_formed_email(self):
        with self.assertRaises(Invalid):
            is_email('')
        with self.assertRaises(Invalid):
            is_email('@google.com')
        with self.assertRaises(Invalid):
            is_email('john.smith+home_work@google')
        good_email = 'john.smith+home_work-02=yahoo.com@gmail.com'
        self.assertEquals(good_email, is_email(good_email))

    def test_is_mobile(self):
        with self.assertRaises(Invalid):
            is_mobile('')
        with self.assertRaises(Invalid):
            is_mobile('013588888888')
        good_phone = '13588888888'
        self.assertEquals(good_phone, is_mobile(good_phone))
        with self.assertRaises(Invalid):
            is_mobile('015988888888')
        good_phone = '15988888888'
        self.assertEquals(good_phone, is_mobile(good_phone))

    def test_is_landline(self):
        with self.assertRaises(Invalid):
            is_landline('')
        for good_phone in ['110', '8888888', '88888888', '8888888-123', '88888888-23435', '0871-8888888-123', '023-88888888-23435', '86-0871-8888888-123', '8888888_123', '023_88888888_23435', '86_0871_8888888_123', '8888888－123', '023－88888888－23435', '86－0871－8888888－123', '86 0871 8888888 123', '86.0871.8888888.123']:
            self.assertEquals(good_phone, is_landline(good_phone))

    def test_is_url(self):
        for bad_url in ['', 'www baidu.com', 'www.baidu.c', 'localhost', 'http://localhost/']:
            with self.assertRaises(Invalid):
                is_url(bad_url)
        for good_url in ['www.baidu.com', 'www.baidu.com/', 'www.baidu.com/s', 'http://www.baidu.com', 'http://www.baidu.com/', 'http://www.baidu.com/s', '192.168.1.1', 'http://192.168.1.1']:
            self.assertEquals(good_url, is_url(good_url))

    def test_validate_date(self):
        date(2007, 07, 30)
        converted = to_date()('2007-7-30')
        self.assertEquals(date(2007, 07, 30), converted)
        converted = to_date(format='%m/%d/%Y')('07/30/2007')
        self.assertEquals(date(2007, 07, 30), converted)
        self.assertIsNone(to_date()(None, return_none_when_invalid=True))
        with self.assertRaises(Invalid):
            to_date()(None)
        self.assertIsNone(to_date(format='%m/%d/%Y')('07-30-2007', return_none_when_invalid=True))
        with self.assertRaises(Invalid):
            to_date(format='%m/%d/%Y')('07-30-2007')

    def test_validate_time(self):
        converted = to_time()('07:30:20')
        self.assertEquals(time(7, 30, 20), converted)

        with self.assertRaises(Invalid):
            to_time()('07.30')

    def test_validate_datetime(self):
        tz = pytz.timezone('Asia/Shanghai')
        self.assertEquals(
            tz.localize(datetime(2011, 07, 01, 0, 10, 0, )).astimezone(pytz.utc), to_datetime()('2011-07-01 00:10:00'))
        with self.assertRaises(Invalid):
            to_datetime()('2011-07-01 00:10')
        with self.assertRaises(Invalid):
            to_datetime(format='%Y-%m-%d')('2011-10-13 10:11')

    def test_validate_datetime_from_iso8601(self):
        converted = to_datetime_with_minute_precision_from_iso8601('2011-07-01 00:10 +08:00')
        self.assertEquals(datetime(2011, 07, 01, 0, 10, 0, tzinfo=pytz.FixedOffset(480)), converted)
        converted = to_datetime_with_minute_precision_from_iso8601('2011-07-01 00:10 +0800')
        self.assertEquals(datetime(2011, 07, 01, 0, 10, 0, tzinfo=pytz.FixedOffset(480)), converted)
        converted = to_datetime_with_minute_precision_from_iso8601('2011-07-01 00:10+0800')
        self.assertEquals(datetime(2011, 07, 01, 0, 10, 0, tzinfo=pytz.FixedOffset(480)), converted)
        converted = to_datetime_with_minute_precision_from_iso8601('2011-07-01 00:10 -08:00')
        self.assertEquals(datetime(2011, 07, 01, 0, 10, 0, tzinfo=pytz.FixedOffset(-480)), converted)

        with self.assertRaises(Invalid):
            to_datetime_with_minute_precision_from_iso8601('2011-07-01 +08:00')
        with self.assertRaises(Invalid):
            to_datetime_with_minute_precision_from_iso8601('2011-07-01 00 +08:00')
        with self.assertRaises(Invalid):
            to_datetime_with_minute_precision_from_iso8601('2011-07-01 00:10:00 +08:00')
        with self.assertRaises(Invalid):
            to_datetime_with_minute_precision_from_iso8601('2011-07-01 00:10 08:00')

    def test_validate_clamp(self):
        self.assertEqual(0, clamp(min=0, max=1)(0))
        with self.assertRaises(Invalid):
            clamp(min=0, max=1)(-1)
        with self.assertRaises(Invalid):
            clamp(min=0, max=1)(2)
        self.assertEqual(1, clamp(min=0, max=1)(1))
        with self.assertRaises(Invalid):
            clamp(min=0, max=1, include_max=False)(1)
        with self.assertRaises(Invalid):
            clamp(min=0, max=1, include_min=False)(0)
