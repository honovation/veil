from __future__ import unicode_literals, print_function, division
from logging import getLogger
from veil_component import *

LOGGER = getLogger(__name__)
subscribers = {}

def publish_event(topic, records_dynamic_dependency=True, **kwargs):
    if records_dynamic_dependency:
        record_dynamic_dependency_consumer(get_loading_component_name(), 'event', topic)
    if topic not in subscribers:
        return
    for subscriber in subscribers[topic]:
        try:
            subscriber(**kwargs)
        except:
            LOGGER.error('failed to publish event:  publishing topic %(topic)s to subscriber %(subscriber)s', {
                'topic': topic,
                'subscriber': subscriber
            })
            raise


def subscribe_event(topic, subscriber):
    record_dynamic_dependency_provider(get_loading_component_name(), 'event', topic)
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