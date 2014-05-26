# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
from veil.environment import VEIL_HOME
from veil.utility.encoding import *
from veil.development.test import *

# imports required in mock functions
from veil.model.collection import DictObject
from veil.utility.clock import get_current_time, get_current_date_in_client_timezone

LOGGER = logging.getLogger(__name__)

def check_live_document():
    live_doc_path = (VEIL_HOME / '文档')
    if not live_doc_path.exists():
        LOGGER.warn('live document directory not found: %(live_doc_path)s', {'live_doc_path': live_doc_path})
        return
    for doc in live_doc_path.walkfiles('*.py'):
        LOGGER.info('checking live document: %(doc)s', {'doc': to_unicode(doc)})
        exec(compile(doc.text(), doc, 'exec'))
        tear_down_fake_test()