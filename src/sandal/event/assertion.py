from __future__ import unicode_literals, print_function, division
from .event import subscribe_event
from .event import unsubscribe_event
from sandal.collection import DictObject
from sandal.collection import single

def assert_event_published(*expected_topics):
    assert expected_topics
    return AssertEventPublishedContext(expected_topics)


class AssertEventPublishedContext(object):
    def __init__(self, expected_topics):
        self.expected_topics = expected_topics
        self.events = []

    def __enter__(self):
        for topic in self.expected_topics:
            subscribe_event(topic, self.on_event_published)
        return self.events

    def __exit__(self, type, value, traceback):
        for topic in self.expected_topics:
            unsubscribe_event(topic, self.on_event_published)
        if not type:
            if not self.events:
                if len(self.expected_topics) == 1:
                    raise Exception('did not publish event {}'.format(single(self.expected_topics)))
                else:
                    raise Exception('did not publish event in any of these topics: {}'.format(self.expected_topics))

    def on_event_published(self, **kwargs):
        self.events.append(DictObject(kwargs))