from __future__ import unicode_literals, print_function, division
import sys
from logging import getLogger

LOGGER = getLogger(__name__)
subscribers = {}

def publish_event(topic, **kwargs):
    if topic not in subscribers:
        return
    for subscriber in subscribers[topic]:
        try:
            subscriber(**kwargs)
        except:
            exc_class, exc, tb = sys.exc_info()
            new_exc = Exception(str('failed to publish event {} to subscriber {}.{}:\n {} {}').format(
                topic, subscriber.__module__, subscriber, exc_class.__name__, exc))
            raise new_exc.__class__, new_exc, tb


def subscribe_event(topic, subscriber):
    subscribers[topic] = subscribers.get(topic, [])
    subscribers[topic].append(subscriber)


def unsubscribe_event(topic, subscriber):
    topic_subscribers = subscribers.get(topic, [])
    if subscriber in topic_subscribers:
        topic_subscribers.remove(subscriber)


def event(topic): #syntax sugar
    def decorator(subscriber):
        subscribe_event(topic, subscriber)
        return subscriber

    return decorator