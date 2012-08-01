from __future__ import unicode_literals, print_function, division
import logging
from veil.backend.redis.client import *
from .item import count_items

LOGGER = logging.getLogger(__name__)
demo_redis = register_redis('demo')

def on_item_created(item_id):
    update_items_count(count_items())


def on_item_deleted(item_id):
    update_items_count(count_items())


def update_items_count(count):
    LOGGER.debug('redis: {}'.format(demo_redis()))
    demo_redis().set('items_count', count)


def get_items_count():
    count = demo_redis().get('items_count')
    return int(count) if count else 0