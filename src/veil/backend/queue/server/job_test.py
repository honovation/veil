from __future__ import unicode_literals, print_function, division
from unittest.case import TestCase
from .job import job

class JobTest(TestCase):
    def test(self):
        self.assertEqual(2, job('some-queue')(lambda a, b: a + b).perform(dict(a=1, b=1)))
