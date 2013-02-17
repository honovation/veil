from __future__ import unicode_literals, print_function, division
from .event import subscribe_event
from .event import unsubscribe_event
from veil.model.collection import DictObject
from veil.model.collection import single

def assert_event_published(*topics):
    assert topics

    def check_events(topics, events):
        if not events:
            if len(topics) == 1:
                raise Exception('did not publish event {}'.format(single(topics)))
            else:
                raise Exception('did not publish event in any of these topics: {}'.format(topics))

    return AssertEventPublishedContext(topics, check_events)


def assert_event_not_published(*topics):
    assert topics

    def check_events(topics, events):
        if events:
            if len(topics) == 1:
                raise Exception('should not publish event {}'.format(single(topics)))
            else:
                raise Exception('should not publish event in any of these topics: {}'.format(topics))

    return AssertEventPublishedContext(topics, check_events)


class AssertEventPublishedContext(object):
    def __init__(self, topics, check_events):
        self.topics = topics
        self.events = []
        self.check_events = check_events

    def __enter__(self):
        for topic in self.topics:
            subscribe_event(topic, self.on_event_published)
        return self.events

    def __exit__(self, type, value, traceback):
        for topic in self.topics:
            unsubscribe_event(topic, self.on_event_published)
        if not type:
            self.check_events(self.topics, self.events)

    def on_event_published(self, **kwargs):
        self.events.append(DictObject(kwargs))