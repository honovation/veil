# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import json
import logging
import socket
from time import sleep
import urllib
import urllib2
from veil.model.collection import *

LOGGER = logging.getLogger(__name__)


def http_call(service, url, data=None, content_type=None, accept=None, accept_charset=None,
        log_data=True, max_tries=1, sleep_at_start=0, sleep_before_retry=0, http_timeout=15):
    if data:
        if content_type and content_type.startswith('application/json'):
            encoded_data = json.dumps(data)
        else:
            encoded_data = urllib.urlencode(data)
    else:
        encoded_data = None
    request = urllib2.Request(url, data=encoded_data)
    if content_type:
        request.add_header('Content-Type', content_type)
    if accept:
        request.add_header('Accept', accept)
    if accept_charset:
        request.add_header('Accept-Charset', accept_charset)
    tries = 1
    if sleep_at_start > 0:
        sleep(sleep_at_start)
    while True:
        try:
            # TODO: urllib2 cannot verify server certificates, use pycurl2 instead
            if http_timeout:
                response = urllib2.urlopen(request, timeout=http_timeout).read()
            else:
                response = urllib2.urlopen(request).read()
        except Exception as e:
            if isinstance(e, urllib2.HTTPError):
                reason = 'cannot fulfill the request'
                if 400 <= e.code < 500: # 4xx, client error, need not retry
                    LOGGER.exception('[%(service)s]failed to get response: %(reason)s, %(url)s, %(headers)s, %(data)s', {
                        'service': service, 'reason': reason, 'url': url, 'headers': request.headers, 'data': request.data if log_data else None
                    })
                    raise
            elif isinstance(e, socket.timeout) or isinstance(e, urllib2.URLError) and isinstance(e.reason, socket.timeout):
                reason = 'timed out'
            elif isinstance(e, urllib2.URLError):
                reason = 'cannot reach the service'
            else:
                reason = 'misc'
            if tries < max_tries:
                tries += 1
                if sleep_before_retry > 0:
                    sleep(sleep_before_retry)
            else:
                LOGGER.exception('[%(service)s]failed to get response: %(reason)s, %(url)s, %(headers)s, %(data)s, %(max_tries)s, %(timeout)s', {
                    'service': service, 'reason': reason, 'url': url, 'headers': request.headers, 'data': request.data if log_data else None,
                    'max_tries': max_tries, 'timeout': http_timeout
                })
                raise
        else:
            LOGGER.info('[%(service)s]succeeded to get response: %(url)s, %(headers)s, %(data)s, %(response)s', {
                'service': service, 'url': url, 'headers': request.headers, 'data': request.data if log_data else None, 'response': response
            })
            if accept == 'application/json':
                response = objectify(json.loads(response))
            return response
