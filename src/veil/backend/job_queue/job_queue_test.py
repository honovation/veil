# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

from datetime import timedelta

from veil.development.test import TestCase
from veil.utility.clock import *
from .job_queue import task


class TaskTest(TestCase):
    def setUp(self):
        super(TaskTest, self).setUp()
        self._ = None

    def test_expired_at(self):
        @task()
        def test_task():
            self._ = 1

        now = get_current_time()
        with require_current_time_being(now):
            test_task.delay(expired_at=now)
            self.assertIsNone(self._)
        with require_current_time_being(now + timedelta(seconds=1)):
            test_task.delay(expired_at=now)
            self.assertIsNone(self._)
        with require_current_time_being(now - timedelta(seconds=1)):
            test_task.delay(expired_at=now)
            self.assertEqual(1, self._)
