from __future__ import unicode_literals, print_function, division
from .event import subscribe_event
from .event import unsubscribe_event
from veil.model.collection import DictObject


def assert_event_published(*event_types):
    assert event_types

    def check_events(event_types, events):
        if not events:
            if len(event_types) == 1:
                raise Exception('did not publish event {}'.format(event_types[0]))
            else:
                raise Exception('did not publish event in any of these topics: {}'.format(event_types))

    return AssertEventPublishedContext(event_types, check_events)


def assert_event_not_published(*event_types):
    assert event_types

    def check_events(event_types, events):
        if events:
            if len(event_types) == 1:
                raise Exception('should not publish event {}'.format(event_types[0]))
            else:
                raise Exception('should not publish event in any of these topics: {}'.format(event_types))

    return AssertEventPublishedContext(event_types, check_events)


class AssertEventPublishedContext(object):
    def __init__(self, event_types, check_events):
        self.event_types = event_types
        self.events = []
        self.check_events = check_events

    def __enter__(self):
        for event_type in self.event_types:
            subscribe_event(event_type, self.on_event_published)
        return self.events

    def __exit__(self, type, value, traceback):
        for event_type in self.event_types:
            unsubscribe_event(event_type, self.on_event_published)
        if not type:
            self.check_events(self.event_types, self.events)

    def on_event_published(self, **kwargs):
        self.events.append(DictObject(kwargs))