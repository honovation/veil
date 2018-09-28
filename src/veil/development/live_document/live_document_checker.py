# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
from veil.environment import VEIL_HOME
from veil.utility.encoding import *
from veil.development.test import *

LOGGER = logging.getLogger(__name__)


def check_live_document():
    live_doc_path = (VEIL_HOME / '文档')
    if not live_doc_path.exists():
        LOGGER.warn('live document directory not found: %(live_doc_path)s', {'live_doc_path': live_doc_path})
        return
    for doc in live_doc_path.walkfiles('*.py'):
        LOGGER.info('checking live document: %(doc)s', {'doc': to_unicode(doc)})
        exec(compile(doc.text(), doc, 'exec'), globals())
        tear_down_fake_test()
