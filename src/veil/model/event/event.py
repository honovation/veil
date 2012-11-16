from __future__ import unicode_literals, print_function, division
import sys
from logging import getLogger
from veil.utility.encoding import *

LOGGER = getLogger(__name__)
subscribers = {}

def publish_event(topic, **kwargs):
    if topic not in subscribers:
        return
    for subscriber in subscribers[topic]:
        try:
            subscriber(**kwargs)
        except:
            LOGGER.error('failed to publish event {} to subscriber {}'.format(topic, subscriber))
            raise


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