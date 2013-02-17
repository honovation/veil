from __future__ import unicode_literals, print_function, division
from veil.development.test import TestCase
from .event import publish_event
from .assertion import assert_event_published
from .event import define_event

EVENT_LUNCH = define_event('lunch')

class EventModuleSmokeTest(TestCase):
    def test(self):
        with assert_event_published(EVENT_LUNCH) as events:
            publish_event(EVENT_LUNCH, food='pizza')
        self.assertEqual(1, len(events))


class PublishEventTest(TestCase):
    def test_no_subscriber(self):
        publish_event(EVENT_LUNCH)

