# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import contextlib
import datetime
import logging
import uuid
from veil.backend.redis import *
from veil.development.test import *
from .tornado import *
from .website_launcher import register_website_context_manager

SESSION_TIMEOUT_IN_SECOND = 60 * 30

LOGGER = logging.getLogger(__name__)
instances = {}

def register_website_session(website):
    redis = register_redis('{}_session'.format(website))
    session = Session(website, redis)
    if website in instances:
        return instances[website]
    instances[website] = session

    @contextlib.contextmanager
    def touch_session():
        session.touch()
        yield

    register_website_context_manager(website, touch_session)
    return session


class Session:
    def __init__(self, website, redis):
        self.website = website
        self.redis = redis

    def touch(self):
        session_id_cookie_name = self.get_session_id_cookie_name()
        session_id = get_cookie(session_id_cookie_name) or self.create_session_id()
        self.redis().hsetnx(session_id, 'session_id', session_id)
        self.redis().expire(session_id, SESSION_TIMEOUT_IN_SECOND)
        expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=SESSION_TIMEOUT_IN_SECOND)
        set_cookie(name=session_id_cookie_name, value=session_id, expires=expires)

    def get(self, key):
        session_id = self.try_get_session_id()
        if not session_id:
            return None
        return self.redis().hget(session_id, key)

    def set(self, key, value):
        session_id = self.try_get_session_id(True)
        self.redis().hset(session_id, key, value)

    def remove(self, key):
        session_id = self.try_get_session_id()
        if session_id:
            return self.redis().hdel(session_id, key)

    def clear(self):
        session_id = self.try_get_session_id()
        if session_id:
            self.redis().delete(session_id)
        clear_cookie(self.get_session_id_cookie_name())

    def try_get_session_id(self, create_if_not_exists=False):
        executing_test = get_executing_test(optional=True)
        if executing_test:
            if getattr(executing_test, 'web_session_id', None):
                return executing_test.web_session_id
            def reset():
                executing_test.web_session_id = None
            executing_test.addCleanup(reset)
            executing_test.web_session_id = self.create_session_id()
            return executing_test.web_session_id
        session_id_cookie_name = self.get_session_id_cookie_name()
        session_id = get_cookie(session_id_cookie_name)
        if not session_id and create_if_not_exists:
            session_id = self.create_session_id()
            expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=SESSION_TIMEOUT_IN_SECOND)
            set_cookie(name=session_id_cookie_name, value=session_id, expires=expires)
        return session_id

    def get_session_id_cookie_name(self):
        return '{}_session_id'.format(self.website)

    def create_session_id(self):
        return '{}-{}'.format(datetime.datetime.now().strftime("%Y%m%d%H%M%S"), str(uuid.uuid4()).replace('-', ''))
