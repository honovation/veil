from __future__ import unicode_literals, print_function, division
from veil.model.test import TestCase
from ..event import publish_event
from ..assertion import assert_event_published

class EventModuleSmokeTest(TestCase):
    def test(self):
        with assert_event_published('lunch') as events:
            publish_event('lunch', food='pizza')
        self.assertEqual(1, len(events))


class PublishEventTest(TestCase):
    def test_no_subscriber(self):
        publish_event('lunch')

