from __future__ import unicode_literals, print_function, division
from logging import getLogger
from veil.model.collection import *
from veil_component import *

LOGGER = getLogger(__name__)
subscribers = {}

def define_event(topic):
    component_name = get_loading_component_name()
    if not component_name:
        raise Exception('event must be defined in component')
    return EventType(component_name=component_name, topic=topic)


def publish_event(event_type, **kwargs):
    topic = get_topic(event_type)
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


def subscribe_event(event_type, subscriber):
    topic = get_topic(event_type)
    subscribers[topic] = subscribers.get(topic, [])
    subscribers[topic].append(subscriber)


def unsubscribe_event(event_type, subscriber):
    topic = get_topic(event_type)
    topic_subscribers = subscribers.get(topic, [])
    if subscriber in topic_subscribers:
        topic_subscribers.remove(subscriber)


def event(event_type): #syntax sugar

    def decorator(subscriber):
        subscribe_event(event_type, subscriber)
        return subscriber

    return decorator


def get_topic(event_type):
    if not isinstance(event_type, EventType):
        raise Exception('is not of type EventType: {}'.format(event_type))
    return event_type.topic


class EventType(DictObject):
    def __init__(self, component_name, topic):
        super(EventType, self).__init__(component_name=component_name, topic=topic)

    def __repr__(self):
        return 'event:{}'.format(self.topic)