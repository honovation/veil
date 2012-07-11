from __future__ import unicode_literals, print_function, division
from unittest.case import TestCase
from ..event import publish_event, subscribe_event, unsubscribe_event
from sandal.fixture import fixtures

class EventModuleSmokeTest(TestCase):
    def test(self):
        with fixtures.assert_event_published('lunch') as events:
            publish_event('lunch', food='pizza')
        self.assertEqual(1, len(events))


class PublishEventTest(TestCase):
    def test_no_subscriber(self):
        publish_event('lunch')

